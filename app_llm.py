import os

# gRPC 로깅 수준 설정 (불필요한 ALTS 로그 메시지 숨기기)
os.environ["GRPC_VERBOSITY"] = "ERROR"

# KoNLPy/JPype 로딩 전, JVM 인코딩 설정 (Windows 환경에서 필수)
os.environ["JAVA_TOOL_OPTIONS"] = "-Dfile.encoding=UTF-8"

import gradio as gr
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import urllib.request
import urllib.parse
import time
import math
from konlpy.tag import Okt
from dotenv import load_dotenv

# .env 파일 로드 (절대 경로 명시)
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path, encoding="utf-8")
else:
    print(".env 파일을 찾을 수 없습니다. API 키가 환경 변수에 설정되었는지 확인하세요.")
from typing import TypedDict, List, Dict
from collections import Counter
from langgraph.graph import StateGraph, END

# Selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from langchain_google_genai import ChatGoogleGenerativeAI


class KnowledgeBase:
    def __init__(self, dic_path="dic"):
        self.dic_path = dic_path
        self._load_dictionaries()

    def _load_dictionaries(self):
        try:
            self.idioms = (
                pd.read_csv(os.path.join(self.dic_path, "idioms.csv"))
                .set_index("phrase")["score"]
                .to_dict()
            )
            self.amplifiers = (
                pd.read_csv(os.path.join(self.dic_path, "amplifiers.csv"))
                .set_index("phrase")["multiplier"]
                .to_dict()
            )
            self.downtoners = (
                pd.read_csv(os.path.join(self.dic_path, "downtoners.csv"))
                .set_index("phrase")["multiplier"]
                .to_dict()
            )
            self.negators = pd.read_csv(os.path.join(self.dic_path, "negators.csv"))[
                "phrase"
            ].tolist()
            self.adjectives = (
                pd.read_csv(os.path.join(self.dic_path, "adjectives.csv"))
                .set_index("phrase")["score"]
                .to_dict()
            )
            self.adverbs = (
                pd.read_csv(os.path.join(self.dic_path, "adverbs.csv"))
                .set_index("phrase")["score"]
                .to_dict()
            )
            self.sentiment_nouns = (
                pd.read_csv(os.path.join(self.dic_path, "sentiment_nouns.csv"))
                .set_index("phrase")["score"]
                .to_dict()
            )
        except FileNotFoundError as e:
            print(f"사전 파일 로드 오류: {e}. 빈 사전으로 시작합니다.")
            self.idioms, self.amplifiers, self.downtoners, self.negators = (
                {},
                {},
                {},
                [],
            )
            self.adjectives, self.adverbs, self.sentiment_nouns = {}, {}, {}


knowledge_base = KnowledgeBase()
okt = Okt()


# LLM 우선 아키텍처를 위한 최종 채점기
class SimpleScorer:
    def __init__(self):
        self.kb = knowledge_base
        self.okt = Okt()
        try:
            self.llm = ChatGoogleGenerativeAI(temperature=0.0, model="gemini-2.5-pro")
        except Exception as e:
            print(
                f"LLM 초기화 오류: {e}. GOOGLE_API_KEY가 .env 파일에 설정되었는지 확인하세요."
            )
            self.llm = None

    def get_dynamic_score(self, sentence_to_score: str, expected_tag: str = None) -> float:
        if not self.llm:
            return 0.0

        try:
            tag_guidance = ""
            if expected_tag:
                tag_guidance = f"\n[참고] 이 표현은 형태소 분석 결과 '{expected_tag}' 품사로 분류되었습니다. 이 정보를 바탕으로 가장 적절한 카테고리 번호를 선택해주세요."

            prompt = f"""
            당신은 한국어 신조어, 관용어, 그리고 감성적인 형용사/부사/명사에 능숙한 감성 분석 전문가입니다. 새로운 구절의 감성 점수를 추론해야 합니다.

            [현재 감성 사전의 예시 및 점수 기준]
            - 점수 범위: -2.0 (매우 부정) ~ 2.0 (매우 긍정) 사이의 실수 값으로 추론해주세요.
            - 긍정적인 단어일수록 높은 양수 값, 부정적인 단어일수록 낮은 음수 값, 중립적인 단어는 0에 가까운 값을 부여해주세요.
            - 강도가 강한 감성 표현일수록 절대값이 큰 점수를 부여해주세요.

            1. 긍정/부정 관용어 (점수): {list(self.kb.idioms.items())[:5]}...
            2. 강조 부사 (점수 배율): {list(self.kb.amplifiers.items())[:5]}...
            3. 완화 부사 (점수 배율): {list(self.kb.downtoners.items())[:5]}...
            4. 부정어: {self.kb.negators[:5]}...
            5. 감성 형용사 (점수): {list(self.kb.adjectives.items())[:5]}...
            6. 감성 부사 (점수): {list(self.kb.adverbs.items())[:5]}...
            7. 감성 명사 (점수): {list(self.kb.sentiment_nouns.items())[:5]}...

            분석할 문장: "{sentence_to_score}"

            [지시사항]
            1. 위 문장에서, 기존 사전에 없는 새로운 '핵심 감성 표현' 구절(phrase)을 딱 하나만 찾아주세요.
            2. '핵심 감성 표현'은 다른 문장에서도 재사용될 수 있는 일반적인 관용어, 신조어, 또는 감성적인 형용사/부사/명사여야 합니다. (예: '가성비 갑', '분위기 깡패', '기대 이상', '황홀하다', '편하게', '만족감')
            3. 문장 전체가 아니라, 그 안의 핵심적인 구절만 정확히 추출해야 합니다.
            4. 만약 문장에 재사용 가능한 특별한 감성 표현이 없다면, '없음'이라고 반환해야 합니다.
            5. 추출한 '핵심 감성 표현'이 1(관용어), 2(강조어), 3(완화어), 4(부정어), 5(형용사), 6(부사), 7(감성 명사) 중 어떤 카테고리에 속하는지, 그리고 그 표현이 문맥에서 가지는 '최종적인 감성 점수'는 얼마가 적절할지 추론해주세요.
            6. '최종적인 감성 점수'는 해당 표현이 문장 내에서 강조어, 완화어, 부정어 등의 영향을 모두 고려한 최종적인 감성 강도여야 합니다.
            7. 만약 추출한 표현이 없더라도, 문장 자체에 긍정 또는 부정 뉘앙스가 있다면, 점수는 0.0이 아닌 약간의 긍정/부정 값(예: 0.3 또는 -0.3)을 부여해야 합니다.
            {tag_guidance}

            [답변 형식]
            '카테고리 번호,핵심 감성 표현,점수' 형식으로만 반환해주세요.
            - 예시 1 (새로운 관용어 발견): 1,분위기 깡패,1.5
            - 예시 2 (새로운 감성 형용사 발견): 5,황홀하다,1.2
            - 예시 3 (감성적이나 관용어/형용사/부사는 없음): 0,없음,0.3
            - 예시 4 (완전 중립): 0,없음,0.0
            """

            response = self.llm.invoke(prompt)
            result = response.content.strip()

            parts = result.split(",")
            if len(parts) != 3:
                return 0.0

            category, phrase, score_str = (
                parts[0].strip(),
                parts[1].strip(),
                parts[2].strip(),
            )
            score = float(score_str)

            # LLM이 새로운 관용어를 학습시킨 경우
            if category == "1" and phrase != "없음":
                print(
                    f"[학습] 새로운 관용어 발견: {phrase} (점수: {score}) -> idioms.csv에 추가"
                )
                with open(
                    os.path.join(self.kb.dic_path, "idioms.csv"),
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    f.write(f"\n{phrase},{score}")
                self.kb.idioms[phrase] = score
                return score

            # LLM이 새로운 증폭어를 학습시킨 경우
            elif category == "2" and phrase != "없음":
                print(
                    f"[학습] 새로운 강조어 발견: {phrase} (배율: {score}) -> amplifiers.csv에 추가"
                )
                with open(
                    os.path.join(self.kb.dic_path, "amplifiers.csv"),
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    f.write(f"\n{phrase},{score}")
                self.kb.amplifiers[phrase] = score
                return 0.0  # 이번 채점에는 반영 안함 (다음부터 적용)

            # LLM이 새로운 완화어를 학습시킨 경우
            elif category == "3" and phrase != "없음":
                print(
                    f"[학습] 새로운 완화어 발견: {phrase} (배율: {score}) -> downtoners.csv에 추가"
                )
                with open(
                    os.path.join(self.kb.dic_path, "downtoners.csv"),
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    f.write(f"\n{phrase},{score}")
                self.kb.downtoners[phrase] = score
                return 0.0  # 이번 채점에는 반영 안함 (다음부터 적용)

            # LLM이 새로운 형용사를 학습시킨 경우
            elif category == "5" and phrase != "없음":
                print(
                    f"[학습] 새로운 감성 형용사 발견: {phrase} (점수: {score}) -> adjectives.csv에 추가"
                )
                with open(
                    os.path.join(self.kb.dic_path, "adjectives.csv"),
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    f.write(f"\n{phrase},{score}")
                self.kb.adjectives[phrase] = score
                return score

            # LLM이 새로운 부사를 학습시킨 경우
            elif category == "6" and phrase != "없음":
                print(
                    f"[학습] 새로운 감성 부사 발견: {phrase} (점수: {score}) -> adverbs.csv에 추가"
                )
                with open(
                    os.path.join(self.kb.dic_path, "adverbs.csv"),
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    f.write(f"\n{phrase},{score}")
                self.kb.adverbs[phrase] = score
                return score

            # LLM이 새로운 감성 명사를 학습시킨 경우
            elif category == "7" and phrase != "없음":
                print(
                    f"[학습] 새로운 감성 명사 발견: {phrase} (점수: {score}) -> sentiment_nouns.csv에 추가"
                )
                with open(
                    os.path.join(self.kb.dic_path, "sentiment_nouns.csv"),
                    "a",
                    newline="",
                    encoding="utf-8",
                ) as f:
                    f.write(f"\n{phrase},{score}")
                self.kb.sentiment_nouns[phrase] = score
                return score

            # LLM이 학습시킬 구절은 없지만, 문장 자체의 뉘앙스 점수를 반환한 경우
            elif category == "0" and phrase == "없음" and score != 0.0:
                return score

            return 0.0

        except Exception as e:
            print(f"LLM 점수 추론 중 오류 발생: {e}")
            return 0.0

    def score_sentence(self, sentence: str, is_positive_context: bool = False, is_negative_context: bool = False):
        final_score = 0.0

        # 1. 초기 점수 설정 (긍정/부정 뉘앙스에 따라 0.3 또는 -0.3)
        if is_positive_context:
            final_score = 0.3
        elif is_negative_context:
            final_score = -0.3

        # ****로 감싸진 핵심 감성 표현 추출
        marked_phrases = re.findall(r'\*\*\*\*([^*]+)\*\*\*\*', sentence)
        negation_factor = 1

        for phrase in marked_phrases:
            phrase = phrase.strip()

            # 2. 기존 관용구로 점수 확인 (가장 높은 우선순위)
            if phrase in self.kb.idioms:
                final_score += self.kb.idioms[phrase]
                continue

            # 3. 강조/완화/부정어 적용
            if phrase in self.kb.amplifiers:
                final_score *= self.kb.amplifiers[phrase]
                continue
            elif phrase in self.kb.downtoners:
                final_score *= self.kb.downtoners[phrase]
                continue
            elif phrase in self.kb.negators:
                negation_factor *= -1
                continue

            # 4. 단어별 감성 점수 누적 및 학습 (형용사, 부사, 명사)
            words_in_phrase = self.okt.pos(phrase, norm=True, stem=True)
            for word, tag in words_in_phrase:
                current_word_score = 0.0
                if tag.startswith("Adjective"):
                    if word in self.kb.adjectives:
                        current_word_score = self.kb.adjectives[word]
                    else:
                        llm_score = self.get_dynamic_score(word, expected_tag=tag)
                        current_word_score = llm_score
                elif tag.startswith("Adverb"):
                    if word in self.kb.adverbs:
                        current_word_score = self.kb.adverbs[word]
                    else:
                        llm_score = self.get_dynamic_score(word, expected_tag=tag)
                        current_word_score = llm_score
                elif tag.startswith("Noun"):
                    if word in self.kb.sentiment_nouns:
                        current_word_score = self.kb.sentiment_nouns[word]
                    else:
                        llm_score = self.get_dynamic_score(word, expected_tag=tag)
                        current_word_score = llm_score

                final_score += current_word_score

        return final_score * negation_factor


# --- LLM 우선 아키텍처를 위한 LangGraph 상태 및 에이전트 ---
class LLMGraphState(TypedDict):
    original_text: str
    keyword: str
    log_details: bool
    llm_summary: str
    final_judgments: List[Dict]


def agent_llm_summarizer(state: LLMGraphState):
    if state["log_details"]:
        print("\n--- [Agent 1: Real LLM Summarizer] 핵심 경험 요약 시작 ---")

    text = state["original_text"]
    keyword = state["keyword"]

    try:
        llm = ChatGoogleGenerativeAI(temperature=0.0, model="gemini-2.5-pro")
        prompt = f"""
        당신은 블로그 리뷰의 핵심 요약 전문가입니다. 아래는 '{keyword}'에 대한 블로그 리뷰 본문입니다.

        본문 전체를 읽고, 글쓴이가 '{keyword}'와 관련하여 경험한 내용 전체에 대한 '긍정적인 점'과 '부정적인 점'을 각각 글머리 기호(bullet points) 형식으로 요약해주세요.

        [매우 중요] 요약할 때, 글쓴이의 감성(긍정/부정)을 명확하게 증폭시키거나 반감시키는 핵심적인 표현(명사, 형용사, 부사, 관용구 등)이 있다면, 해당 표현을 ****로 감싸서 표시해주세요.
        예시: "이 축제는 ****정말**** ****환상적****이었어요." 또는 "음식이 ****너무**** ****별로****였어요."
        - ****는 감성 강도에 명확하게 영향을 미치는 표현에만 사용해야 합니다.
        - 감성 강도에 영향을 미치지 않는 일반적인 단어에는 ****를 사용하지 마세요.

        [참고] 감성 표현 사전 예시:
        - 관용어: {list(knowledge_base.idioms.keys())[:5]}...
        - 강조어: {list(knowledge_base.amplifiers.keys())[:5]}...
        - 완화어: {list(knowledge_base.downtoners.keys())[:5]}...
        - 부정어: {knowledge_base.negators[:5]}...
        - 감성 형용사: {list(knowledge_base.adjectives.keys())[:5]}...
        - 감성 부사: {list(knowledge_base.adverbs.keys())[:5]}...
        - 감성 명사: {list(knowledge_base.sentiment_nouns.keys())[:5]}...

        (예: 원문이 '정말 맛있다'이면, 요약도 '정말 맛있다'여야 합니다. '맛있다'로 줄이면 안 됩니다.)

        - 긍정적인 점:
          - (여기에 긍정적인 경험 요약)
        - 부정적인 점:
          - (여기에 부정적인 경험 요약)

        다른 부가적인 설명 없이, 위 형식에 맞춰 요약만 제공해주세요.

        --- 블로그 본문 시작 ---
        {text}
        --- 블로그 본문 끝 ---
        """

        response = llm.invoke(prompt)
        summary = response.content.strip()

    except Exception as e:
        print(f"LLM 요약 중 오류 발생: {e}")
        summary = ""

    if state["log_details"]:
        print("--- LLM 핵심 경험 요약 결과 ---")
        print(summary if summary else "[요약할 내용이 없습니다]")
        print("---------------------------")

    return {"llm_summary": summary}


def agent_rule_scorer_on_summary(state: LLMGraphState):
    if state["log_details"]:
        print("\n--- [Agent 2: Rule Scorer] 요약 기반 점수 계산 시작 ---")

    summary = state["llm_summary"]
    scorer = SimpleScorer()
    sentences = [s for s in summary.split("\n") if s.strip()]

    final_judgments = []
    is_positive_context = False
    is_negative_context = False

    for sentence in sentences:
        if sentence.strip() == "- 긍정적인 점:":
            is_positive_context = True
            is_negative_context = False
            if state["log_details"]:
                print(f"  [필터링] 헤더 문장 제외: {sentence}")
            continue
        elif sentence.strip() == "- 부정적인 점:":
            is_positive_context = False
            is_negative_context = True
            if state["log_details"]:
                print(f"  [필터링] 헤더 문장 제외: {sentence}")
            continue

        score = scorer.score_sentence(sentence, is_positive_context=is_positive_context, is_negative_context=is_negative_context)
        verdict = "중립"
        if score > 0.1:
            verdict = "긍정"
        elif score < -0.1:
            verdict = "부정"

        final_judgments.append(
            {"sentence": sentence, "final_verdict": verdict, "score": score}
        )
        if state["log_details"]:
            print(f"  [{verdict}] 점수: {score:.2f} | 문장: {sentence}")

    return {"final_judgments": final_judgments}


# LLM 우선 워크플로우 정의
llm_workflow = StateGraph(LLMGraphState)
llm_workflow.add_node("llm_summarizer", agent_llm_summarizer)
llm_workflow.add_node("rule_scorer", agent_rule_scorer_on_summary)
llm_workflow.add_edge("llm_summarizer", "rule_scorer")
llm_workflow.add_edge("rule_scorer", END)
llm_workflow.set_entry_point("llm_summarizer")
app_llm_graph = llm_workflow.compile()

# --- 웹 스크래핑 및 UI 코드 (기존 app.py와 거의 동일) ---
PAGE_SIZE = 10


def search_naver_blog_page(query, start_index=1):
    NAVER_BLOG_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
    NAVER_BLOG_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
    if not NAVER_BLOG_CLIENT_ID or not NAVER_BLOG_CLIENT_SECRET:
        raise ValueError(".env 파일에 네이버 API 키를 설정하세요.")
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/blog.json?query={encText}&display=100&start={start_index}"
    headers = {
        "X-Naver-Client-Id": NAVER_BLOG_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_BLOG_CLIENT_SECRET,
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])
    except requests.exceptions.RequestException as e:
        print(f"API 호출 오류: {e}")
        return []


def parse_component_text(element):
    text = element.get_text(strip=True)
    if not text:
        return []
    if all(c in ".-_~*# " for c in text):
        return []
    if text.startswith("#"):
        return []
    sentences = re.split(r"(?<=[.?!~…])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def scrape_blog_content(driver, url: str) -> str:
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(
            EC.frame_to_be_available_and_switch_to_it((By.NAME, "mainFrame"))
        )
        try:
            content_element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.se-main-container")
                )
            )
        except TimeoutException:
            content_element = driver.find_element(By.CSS_SELECTOR, "div#postViewArea")

        html_content = content_element.get_attribute("innerHTML")
        soup = BeautifulSoup(html_content, "html.parser")

        parsed_sentences = []
        components = soup.find_all("div", class_="se-component", recursive=False)
        if not components:
            components = soup.select("div.se-component")

        for component in components:
            if "se-text" in component.get("class", []):
                parsed_sentences.extend(parse_component_text(component))
            elif "se-image" in component.get("class", []):
                caption = component.select_one(".se-caption")
                if caption:
                    parsed_sentences.extend(parse_component_text(caption))
            elif "se-list" in component.get("class", []):
                list_items = component.select("li")
                for li in list_items:
                    parsed_sentences.extend(parse_component_text(li))
            elif "se-quote" in component.get("class", []):
                parsed_sentences.extend(parse_component_text(component))
            elif "se-map" in component.get("class", []):
                map_title = component.select_one(".se-map-title")
                if map_title:
                    parsed_sentences.extend(parse_component_text(map_title))
            elif "se-oglink" in component.get("class", []):
                link_title = component.select_one(".se-oglink-title")
                if link_title:
                    parsed_sentences.extend(parse_component_text(link_title))
            elif "se-table" in component.get("class", []):
                cells = component.select("td, th")
                for cell in cells:
                    parsed_sentences.extend(parse_component_text(cell))

        final_sentences = []
        greeting_pattern = re.compile(r"^(안녕하세요|여러분|구독자님)")
        closing_pattern = re.compile(r"(감사합니다|구독과|좋아요|알림 설정)")
        for i, sentence in enumerate(parsed_sentences):
            sentence = re.sub(r"\s+", " ", sentence).strip()
            sentence = sentence.replace("\u200b", "")
            if i < 2 and greeting_pattern.search(sentence):
                continue
            if i > len(parsed_sentences) - 3 and closing_pattern.search(sentence):
                continue
            if sentence:
                final_sentences.append(sentence)

        if not final_sentences:
            return content_element.text

        return "\n".join(final_sentences)

    except TimeoutException:
        return (
            "오류: mainFrame을 찾거나 컨텐츠를 로드하는 데 시간이 너무 오래 걸립니다."
        )
    except Exception as e:
        return f"크롤링 중 오류: {e}"
    finally:
        driver.switch_to.default_content()


def change_page(full_df, page_num):
    page_num = int(page_num)
    total_rows = len(full_df)
    total_pages = math.ceil(total_rows / PAGE_SIZE) if total_rows > 0 else 1
    page_num = max(1, min(page_num, total_pages))
    start_idx = (page_num - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    return full_df.iloc[start_idx:end_idx], page_num, f"/ {total_pages}"


def analyze_keyword_and_generate_report(
    keyword: str, progress=gr.Progress(track_tqdm=True)
):
    if not keyword:
        return "키워드를 입력해주세요.", None, None, None, 1, "/ 1"

    progress(0, desc="웹 드라이버 설정 중...")
    service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        valid_blogs_data, total_searched = [], 0
        start_index = 1
        progress(0, desc="네이버 블로그 검색 시작...")
        while len(valid_blogs_data) < 3 and start_index <= 901:
            progress(
                len(valid_blogs_data) / 3,
                desc=f"API 검색 중 ({len(valid_blogs_data)}/3 확보, {start_index}번부터)",
            )
            api_results = search_naver_blog_page(keyword, start_index=start_index)
            if not api_results:
                break
            total_searched += len(api_results)
            for item in api_results:
                if "blog.naver.com" in item["link"]:
                    item["content"] = scrape_blog_content(driver, item["link"])
                    valid_blogs_data.append(item)
                    if len(valid_blogs_data) >= 3:
                        break
            start_index += 100

        progress(0.8, desc="LangGraph 에이전트 분석 수행 중...")
        results = []
        for blog_data in valid_blogs_data:
            content = blog_data.get("content", "")
            if "오류" in content or "찾을 수 없습니다" in content:
                num_pos, num_neg, num_neu, display_content = 0, 0, 0, content
            else:
                # 모든 블로그에 대해 상세 로그를 출력하도록 수정
                final_state = app_llm_graph.invoke(
                    {"original_text": content, "keyword": keyword, "log_details": True}
                )
                judgments = [
                    res["final_verdict"] for res in final_state["final_judgments"]
                ]
                num_pos, num_neg, num_neu = (
                    judgments.count("긍정"),
                    judgments.count("부정"),
                    judgments.count("중립"),
                )
                display_sentences = [
                    f"[{res['final_verdict']}] {res['sentence']}"
                    for res in final_state["final_judgments"]
                ]
                display_content = "\n---\n".join(display_sentences)
            total_sentences = num_pos + num_neg
            pos_ratio = (num_pos / total_sentences * 100) if total_sentences > 0 else 0
            results.append(
                {
                    "블로그 제목": blog_data["title"],
                    "링크": blog_data["link"],
                    "긍정 문장 수": num_pos,
                    "부정 문장 수": num_neg,
                    "중립 문장 수": num_neu,
                    "긍정 비율 (%)": f"{pos_ratio:.1f}",
                    "긍/부정 문장 요약": display_content,
                }
            )

        results_df = pd.DataFrame(results)
        url_list = [f"- [{b['title']}]({b['link']})" for b in valid_blogs_data]
        url_markdown = (
            f"### 수집된 블로그 URL ({len(valid_blogs_data)}개)\n" + "\n".join(url_list)
        )

        total_pages = (
            math.ceil(len(results_df) / PAGE_SIZE) if not results_df.empty else 1
        )
        initial_page_df, _, total_pages_str = change_page(results_df, 1)
        progress(1, desc="완료!")
        return (
            f"총 {total_searched}개 검색, {len(valid_blogs_data)}개 네이버 블로그 분석 완료.",
            initial_page_df,
            url_markdown,
            results_df,
            1,
            total_pages_str,
        )
    finally:
        driver.quit()


with gr.Blocks(title="LLM 우선 감성 분석기") as demo:
    gr.Markdown("# LLM 우선 네이버 블로그 감성 분석기")
    gr.Markdown(
        "LLM 에이전트가 먼저 블로그 본문에서 핵심 경험을 요약한 후, 규칙 기반으로 점수를 계산하는 새로운 아키텍처입니다."
    )
    full_results_df_state, current_page_state, total_pages_state = (
        gr.State(),
        gr.State(1),
        gr.State(1),
    )
    with gr.Row():
        keyword_input = gr.Textbox(
            label="검색어", placeholder="예: 제주도 핫플", scale=3
        )
        analyze_button = gr.Button("분석 시작", variant="primary", scale=1)
    status_output = gr.Textbox(label="분석 상태")
    url_list_output = gr.Markdown(label="수집된 전체 URL 리스트")
    results_output = gr.DataFrame(
        label="개별 블로그 분석 결과",
        headers=[
            "블로그 제목",
            "링크",
            "긍정 문장 수",
            "부정 문장 수",
            "중립 문장 수",
            "긍정 비율 (%)",
            "긍/부정 문장 요약",
        ],
        wrap=True,
    )
    with gr.Row(elem_id="pagination", variant="panel"):
        first_page_button, prev_page_button = gr.Button("<< 맨 처음"), gr.Button(
            "< 이전"
        )
        page_number_input = gr.Number(
            label="", value=1, interactive=True, precision=0, minimum=1
        )
        total_pages_output = gr.Textbox(label="/", interactive=False, max_lines=1)
        next_page_button, last_page_button = gr.Button("다음 >"), gr.Button("맨 끝 >>")

    analyze_button.click(
        fn=analyze_keyword_and_generate_report,
        inputs=[keyword_input],
        outputs=[
            status_output,
            results_output,
            url_list_output,
            full_results_df_state,
            page_number_input,
            total_pages_output,
        ],
    )

    def pg_change(df, page):
        return change_page(df, page)

    first_page_button.click(
        fn=lambda df: pg_change(df, 1),
        inputs=[full_results_df_state],
        outputs=[results_output, page_number_input, total_pages_output],
    )
    prev_page_button.click(
        fn=lambda df, c: pg_change(df, c - 1),
        inputs=[full_results_df_state, current_page_state],
        outputs=[results_output, page_number_input, total_pages_output],
    )
    next_page_button.click(
        fn=lambda df, c, t: pg_change(df, min(c + 1, t)),
        inputs=[full_results_df_state, current_page_state, total_pages_state],
        outputs=[results_output, page_number_input, total_pages_output],
    )
    last_page_button.click(
        fn=lambda df, t: pg_change(df, t),
        inputs=[full_results_df_state, total_pages_state],
        outputs=[results_output, page_number_input, total_pages_output],
    )
    page_number_input.submit(
        fn=pg_change,
        inputs=[full_results_df_state, page_number_input],
        outputs=[results_output, page_number_input, total_pages_output],
    )
    page_number_input.change(
        lambda x: x, inputs=page_number_input, outputs=current_page_state
    )
    total_pages_output.change(
        lambda x: (
            int(x.replace("/", "").strip())
            if x and x.replace("/", "").strip().isdigit()
            else 1
        ),
        inputs=total_pages_output,
        outputs=total_pages_state,
    )

if __name__ == "__main__":
    print("Gradio 앱을 시작합니다. 브라우저에서 UI를 확인하세요.")
    print(
        "이제 Selenium과 webdriver-manager가 필요합니다. 'pip install -r requirements.txt'를 실행해주세요."
    )
    print(
        "네이버 API 키(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)가 .env 파일에 설정되어 있어야 합니다."
    )
    demo.launch()
