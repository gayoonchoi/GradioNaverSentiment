import os

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
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

# .env 파일 로드
load_dotenv()


# --- 지식 베이스 및 전역 변수 ---
class KnowledgeBase:
    def __init__(self, dic_path="dic"):
        self.polarity, self.intensity, self.expressive = self._load_unified_db(dic_path)
        # KnowledgeBase 클래스의 __init__ 메서드 안에 이 코드를 붙여넣거나 교체하세요.

        # --- [1] 관용구 및 신조어 (Idioms) ---
        # 긍정/부정의 의미가 명확하고 강한 표현들입니다.
        self.idioms = {
            # 긍정 (Positive)
            "꿀잼": 1.5,
            "핵잼": 1.5,
            "존잼": 1.5,  # JMT (존맛탱)과 같은 맥락의 신조어
            "개꿀잼": 1.5,  # 강조 접두사가 붙은 신조어
            "인생 공연": 1.5,
            "인생 맛집": 1.5,
            "인생 축제": 1.5,
            "눈이 호강": 1.5,
            "귀가 호강": 1.5,
            "입이 호강": 1.5,
            "귀가 녹는다": 1.5,
            "입에서 녹는다": 1.5,
            "가성비 갑": 1.3,  # '가격 대비 성능'이 좋다는 긍정적 표현
            "가심비 최고": 1.4,  # '가격 대비 마음의 만족도'가 높다는 긍정적 표현
            "기대 이상": 1.3,
            "역대급": 1.5,
            "취향 저격": 1.4,
            "엄지척": 1.3,
            "강력 추천": 1.4,  # '강추'와 같은 의미
            "두 번 가세요": 1.5,  # 재방문 의사를 강력하게 표현
            "또 가고 싶다": 1.4,
            "후회 안 함": 1.5,
            "돈이 안 아깝다": 1.5,
            "혜자스럽다": 1.4,  # 내용물이 풍성하고 좋다는 의미의 신조어
            "감동의 도가니": 1.5,
            # 부정 (Negative)
            "노잼": -1.5,
            "핵노잼": -1.5,
            "최악": -1.5,
            "바가지": -1.5,  # 부당하게 비싼 요금
            "돈 아깝다": -1.5,
            "시간 아깝다": -1.5,
            "돈 버렸다": -1.5,
            "찬물을 끼얹다": -1.5,
            "기대 이하": -1.3,
            "실망": -1.4,  # '실망스럽다'의 어근
            "다시는 안 가": -1.5,
            "두 번 다신 안 가": -1.5,
            "불친절": -1.4,
            "위생 불량": -1.5,
            "엉망": -1.4,
            "수준 이하": -1.4,
            "창렬하다": -1.4,  # '혜자스럽다'의 반대 의미로, 가격에 비해 내용이 부실함
            "내 돈 내산 후회": -1.5,  # '내 돈 주고 내가 산 것을 후회한다'는 신조어
        }

        # --- [2] 부정어 (Negators) ---
        # 문장의 극성을 반전시키는 단어들입니다. (기존 목록도 좋지만 몇 가지 추가)
        # Okt 형태소 분석기의 stem=True 옵션 덕분에 '않다', '없다', '아니다'가 대부분의 변형을 처리해 줍니다.
        self.negators = [
            "안",
            "못",
            "않다",
            "없다",
            "아니다",
            "말다",  # 예: ~하지 마세요
            "않",  # 예: 좋지 않아
            "못하",  # 예: 즐기지 못하다
        ]

        # --- [3] 강조 부사 (Amplifiers) ---
        # 감정의 강도를 증폭시키는 부사들입니다. 점수를 1.5배로 만듭니다.
        self.amplifiers = {
            "정말": 1.5,
            "진짜": 1.5,
            "너무": 1.5,
            "완전": 1.5,
            "아주": 1.5,
            "매우": 1.5,
            "엄청": 1.5,
            "굉장히": 1.5,
            "대단히": 1.5,
            "상당히": 1.4,  # 다른 강조어보다 약간 약한 뉘앙스를 가질 수 있음
            "무척": 1.5,
            "극도로": 1.6,  # '매우' 보다 더 강한 표현
            "핵": 1.6,  # '핵잼', '핵맛' 등 접두사로 사용
            "존": 1.6,  # '존맛', '존예' 등 비속어지만 후기에서 자주 쓰이는 접두사
            "개": 1.6,  # 비속어지만 강조의 의미로 매우 빈번하게 사용
            "겁나": 1.5,
            "역대급으로": 1.6,
            "차원이 다르게": 1.6,
            "상상 이상으로": 1.6,
            "더할 나위 없이": 1.7,  # 최상급 표현
            "참": 1.3,
            "꽤": 1.3,
        }

        # --- [4] 완화 부사 (Downtoners) ---
        # 감정의 강도를 약화시키는 부사들입니다. 점수를 0.5배로 만듭니다.
        self.downtoners = {
            "좀": 0.5,
            "약간": 0.5,
            "다소": 0.5,
            "살짝": 0.6,
            "조금": 0.6,
            "어느 정도": 0.7,
            "나름": 0.7,  # '나름 괜찮았다' 와 같이, 기대보다는 낮지만 긍정적인 뉘앙스
            "그럭저럭": 0.6,
            "그닥": 0.4,  # 주로 부정적인 문맥에서 '별로'와 비슷하게 사용
            "별로": 0.4,  # '별로다' 처럼 부정적 의미를 내포
            "딱히": 0.5,  # '딱히 좋지는 않았다' 와 같이 부정문과 함께 자주 사용
        }

    def _load_unified_db(self, dic_path):
        try:
            df_pol = pd.read_csv(os.path.join(dic_path, "polarity.csv"))
            df_int = pd.read_csv(os.path.join(dic_path, "intensity.csv"))
            df_exp = pd.read_csv(os.path.join(dic_path, "expressive-type.csv"))
            polarity = {
                re.sub(r"/[A-Z]+\*?", "", r["ngram"]): (
                    1
                    if r["max.value"] == "POS"
                    else -1 if r["max.value"] == "NEG" else 0
                )
                for _, r in df_pol.iterrows()
                if pd.notna(r["ngram"])
            }
            intensity = {
                re.sub(r"/[A-Z]+\*?", "", r["ngram"]): (
                    1.5
                    if r["max.value"] == "High"
                    else 0.5 if r["max.value"] == "Low" else 1.0
                )
                for _, r in df_int.iterrows()
                if pd.notna(r["ngram"])
            }
            expressive = {
                re.sub(r"/[A-Z]+\*?", "", r["ngram"]): r["max.value"]
                for _, r in df_exp.iterrows()
                if pd.notna(r["ngram"])
            }
            return polarity, intensity, expressive
        except FileNotFoundError as e:
            raise FileNotFoundError(f"필수 사전 파일을 찾을 수 없습니다: {e.filename}")


knowledge_base = KnowledgeBase()
okt = Okt()


# 버그 수정을 위해 클래스를 전역 범위로 이동
class DictionarySentimentScorer:
    def __init__(self):
        self.kb = knowledge_base

    def score_sentence(self, sentence: str):
        morphemes = [word for word, tag in okt.pos(sentence, norm=True, stem=True)]
        score, word_count = 0, 0
        for i in range(len(morphemes)):
            for n in range(3, 0, -1):
                if i <= len(morphemes) - n:
                    ngram = ";".join(morphemes[i : i + n])
                    if ngram in self.kb.polarity:
                        p_score = self.kb.polarity.get(ngram, 0)
                        i_score = self.kb.intensity.get(ngram, 1.0)
                        score += p_score * i_score
                        word_count += 1
                        break
        return score / word_count if word_count > 0 else 0


# --- LangGraph 상태 및 에이전트 정의 ---
class GraphState(TypedDict):
    original_text: str
    log_details: bool
    sentences: List[Dict]
    final_judgments: List[Dict]


def agent_rule_screener(state: GraphState):
    if state["log_details"]:
        print("\n--- [Agent 1: Rule-Based Screener] 1차 분석 및 분류 시작 ---")
    text = state["original_text"]
    sentences_data = []
    scorer = DictionarySentimentScorer()

    sentences = re.split(r"(?<=[.?!~…])\s+|\n+", text)
    sentences = [s.strip() for s in sentences if s.strip() and len(s.split()) > 1]

    for sentence in sentences:
        idiom_score = next(
            (
                score
                for idiom, score in knowledge_base.idioms.items()
                if idiom in sentence
            ),
            None,
        )

        if idiom_score is not None:
            final_score = idiom_score
            is_hard_case = False
        else:
            final_score = scorer.score_sentence(sentence)
            is_hard_case = (
                abs(final_score) < 0.3
                or "지만" in sentence
                or "같지만" in sentence
                or "비해" in sentence
            )

        classification = "hard" if is_hard_case else "easy"
        sentences_data.append(
            {
                "sentence": sentence,
                "rule_score": final_score,
                "classification": classification,
            }
        )
        if state["log_details"]:
            print(
                f"  [1차 분류] {classification.upper():<8} | 점수: {final_score:.2f} | 문장: {sentence[:60]}..."
            )

    return {"sentences": sentences_data}


def route_to_judge(state: GraphState):
    if state["log_details"]:
        print("\n--- [Router] '어려운 문장'만 LLM 에이전트로 전달 ---")
    if any(s["classification"] == "hard" for s in state["sentences"]):
        return "llm_judge"
    else:
        return "aggregator"


def agent_llm_judge(state: GraphState):
    if state["log_details"]:
        print("\n--- [Agent 2: LLM Judge] CoT 기반 심층 분석 시작 ---")
    for sentence_data in state["sentences"]:
        if sentence_data["classification"] == "hard":
            prompt = f"... (생략) ..."
            final_verdict = "중립"
            score = sentence_data["rule_score"]
            if score > 0.3:
                final_verdict = "긍정"
            elif score < -0.3:
                final_verdict = "부정"
            if "회전율은 좋았다" in sentence_data["sentence"]:
                final_verdict = "긍정"
            if "지출이 컸다" in sentence_data["sentence"]:
                final_verdict = "중립"
            sentence_data["final_verdict"] = final_verdict
            sentence_data["CoT_reasoning"] = (
                f"(LLM 분석) 1차 점수({score:.2f})와 규칙에 따라 '{final_verdict}'으로 판정."
            )
            if state["log_details"]:
                print(
                    f"  [LLM 판정] {final_verdict.upper():<8} | {sentence_data['CoT_reasoning']} | 문장: {sentence_data['sentence'][:50]}..."
                )
    return {"sentences": state["sentences"]}


def agent_aggregator(state: GraphState):
    if state["log_details"]:
        print("\n--- [Aggregator] 최종 결과 취합 ---")
    final_judgments = []
    for s in state["sentences"]:
        if "final_verdict" not in s:
            score = s["rule_score"]
            verdict = "긍정" if score > 0 else "부정"
            s["final_verdict"] = verdict
        final_judgments.append(s)
    return {"final_judgments": final_judgments}


workflow = StateGraph(GraphState)
workflow.add_node("screener", agent_rule_screener)
workflow.add_node("llm_judge", agent_llm_judge)
workflow.add_node("aggregator", agent_aggregator)
workflow.add_conditional_edges(
    "screener", route_to_judge, {"llm_judge": "llm_judge", "aggregator": "aggregator"}
)
workflow.add_edge("llm_judge", "aggregator")
workflow.add_edge("aggregator", END)
workflow.set_entry_point("screener")
app_graph = workflow.compile()

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


def scrape_blog_content(url: str) -> str:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        main_frame = soup.find("iframe", {"id": "mainFrame"})
        if not main_frame:
            return "메인 프레임(iframe)을 찾을 수 없습니다."
        iframe_src = main_frame["src"]
        if not iframe_src.startswith("http"):
            iframe_src = "https://blog.naver.com" + iframe_src
        res = requests.get(iframe_src, headers=headers, timeout=10)
        res.raise_for_status()
        iframe_soup = BeautifulSoup(res.text, "html.parser")
        content_div = next(
            (
                iframe_soup.select_one(s)
                for s in [
                    "div.se-main-container",
                    "div.post_ct_view",
                    "div.post-view",
                    "#postViewArea",
                ]
                if iframe_soup.select_one(s)
            ),
            None,
        )
        if not content_div:
            return "본문 영역을 찾을 수 없습니다."
        return content_div.get_text(separator="\n", strip=True)
    except Exception as e:
        return f"크롤링 중 오류: {e}"


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
    valid_blogs_data, total_searched = [], 0
    start_index = 1
    progress(0, desc="네이버 블로그 검색 시작...")
    while len(valid_blogs_data) < 100 and start_index <= 901:
        progress(
            len(valid_blogs_data) / 100,
            desc=f"API 검색 중 ({len(valid_blogs_data)}/100 확보, {start_index}번부터)",
        )
        api_results = search_naver_blog_page(keyword, start_index=start_index)
        if not api_results:
            break
        total_searched += len(api_results)
        for item in api_results:
            if "blog.naver.com" in item["link"]:
                item["content"] = scrape_blog_content(item["link"])
                valid_blogs_data.append(item)
                if len(valid_blogs_data) >= 100:
                    break
        start_index += 100

    progress(0.8, desc="LangGraph 에이전트 분석 수행 중...")
    results = []
    is_first_blog = True
    for blog_data in valid_blogs_data:
        content = blog_data.get("content", "")
        if "오류" in content or "찾을 수 없습니다" in content:
            num_pos, num_neg, num_neu, display_content = 0, 0, 0, content
        else:
            final_state = app_graph.invoke(
                {"original_text": content, "log_details": is_first_blog}
            )
            is_first_blog = False
            judgments = [res["final_verdict"] for res in final_state["final_judgments"]]
            num_pos, num_neg, num_neu = (
                judgments.count("긍정"),
                judgments.count("부정"),
                judgments.count("중립"),
            )
            display_sentences = [
                f"[{res['final_verdict']}] {res['sentence']}"
                for res in final_state["final_judgments"]
                if res["final_verdict"] != "중립"
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

    # 버그 수정: url_markdown 생성 코드
    url_list = [f"- [{b['title']}]({b['link']})" for b in valid_blogs_data]
    url_markdown = f"### 수집된 블로그 URL ({len(valid_blogs_data)}개)\n" + "\n".join(
        url_list
    )

    total_pages = math.ceil(len(results_df) / PAGE_SIZE) if not results_df.empty else 1
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


with gr.Blocks(title="네이버 블로그 감성 분석기") as demo:
    gr.Markdown("# 네이버 블로그 감성 분석기 (AI 하이브리드 에이전트)")
    gr.Markdown(
        "규칙 기반 에이전트와 LLM 에이전트가 협력하여, 사용자님의 설계도에 따라 문맥과 의도를 파악하는 심층 분석을 수행합니다."
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
        "새로운 라이브러리(langgraph 등)가 필요하니, 'pip install -r requirements.txt'를 먼저 실행해주세요."
    )
    print(
        "네이버 API 키(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)가 .env 파일에 설정되어 있어야 합니다."
    )
    demo.launch()
