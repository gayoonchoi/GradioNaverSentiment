import gradio as gr
import pandas as pd
import re
import math
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.application.graph import app_llm_graph
from src.infrastructure.web.naver_api import search_naver_blog_page
from src.infrastructure.web.scraper import scrape_blog_content
from src.infrastructure.reporting.charts import create_donut_chart, create_stacked_bar_chart
from src.infrastructure.reporting.files import save_summary_to_csv
from src.infrastructure.llm_client import get_llm_client

PAGE_SIZE = 10

def change_page(full_df, page_num):
    if full_df is None or full_df.empty:
        return pd.DataFrame(), 1, "/ 1"
    page_num = int(page_num)
    total_rows = len(full_df)
    total_pages = math.ceil(total_rows / PAGE_SIZE) if total_rows > 0 else 1
    page_num = max(1, min(page_num, total_pages))
    start_idx = (page_num - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    return full_df.iloc[start_idx:end_idx], page_num, f"/ {total_pages}"

def get_season(postdate: str) -> str:
    month = int(postdate[4:6])
    if month in [3, 4, 5]: return "봄"
    elif month in [6, 7, 8]: return "여름"
    elif month in [9, 10, 11]: return "가을"
    else: return "겨울"

def summarize_negative_feedback(sentences: list) -> str:
    """LLM을 사용하여 부정적인 피드백 문장들을 요약합니다."""
    if not sentences:
        return ""
    
    llm = get_llm_client(model="gemini-2.5-pro")
    
    # 중복 제거
    unique_sentences = sorted(list(set(sentences)), key=len, reverse=True)

    prompt = f"""
    아래는 서비스/장소에 대한 여러 블로그 리뷰에서 수집된 부정적인 의견들입니다. 
    이 의견들을 종합하여 사용자가 겪은 주요 불만 사항들을 1., 2., 3. ... 형식의 목록으로 요약해주세요.
    - 비슷한 내용의 의견은 하나로 묶어서 대표적인 불만 사항으로 만들어주세요.
    - 각 항목은 사용자가 어떤 점을 왜 부정적으로 느꼈는지 명확히 드러나도록 간결하게 작성해주세요.
    - 최소 3개, 최대 10개의 주요 불만 사항으로 요약해주세요.

    [수집된 부정적인 의견]
    - {"\n- ".join(unique_sentences)}

    [주요 불만 사항 요약]
    """
    
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"부정적 의견 요약 중 오류 발생: {e}")
        return "부정적 의견을 요약하는 데 실패했습니다."

def save_negative_summary_to_csv(summary_text: str, keyword: str) -> str:
    """요약된 부정적 피드백을 CSV 파일로 저장합니다."""
    if not summary_text or "실패했습니다" in summary_text:
        return None
        
    # "1.", "2." 등 숫자와 점으로 시작하는 라인 추출
    items = re.findall(r"^\d+\.\s*(.*)", summary_text, re.MULTILINE)
    
    if not items:
        return None

    df = pd.DataFrame(items, columns=["주요 불만 사항"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_keyword = re.sub(r'[\\/*?"<>|]', '', keyword)
    csv_filepath = f"{sanitized_keyword}_negative_summary_{timestamp}.csv"
    df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
    return csv_filepath

def _perform_analysis(keyword: str, num_reviews: int, driver, progress_desc: str, progress: gr.Progress):
    if not keyword:
        return {"error": "키워드를 입력해주세요."}

    search_keyword = f"{keyword} 후기"
    max_candidates = max(50, num_reviews * 8)
    candidate_blogs = []
    total_searched = 0
    start_index = 1
    
    progress(0, desc=f"[{progress_desc}] '{search_keyword}'로 블로그 검색 중...")
    while len(candidate_blogs) < max_candidates and start_index <= 901:
        api_results = search_naver_blog_page(search_keyword, start_index=start_index)
        if not api_results: break
        total_searched += len(api_results)
        for item in api_results:
            if "blog.naver.com" in item["link"]:
                item['title'] = re.sub(r'<[^>]+>', '', item['title'])
                candidate_blogs.append(item)
                if len(candidate_blogs) >= max_candidates: break
        start_index += 100

    if not candidate_blogs:
        return {"error": f"'{search_keyword}'에 대한 네이버 블로그를 찾을 수 없습니다."}

    valid_blogs_data, results, all_negative_sentences = [], [], []
    total_pos_sentences, total_neg_sentences = 0, 0
    seasonal_data = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}}
    
    for i, blog_data in enumerate(candidate_blogs):
        progress((i + 1) / len(candidate_blogs), desc=f"[{progress_desc}] 후보 {i+1}/{len(candidate_blogs)} 검증 중... ({len(valid_blogs_data)}/{num_reviews} 완료)")

        content = scrape_blog_content(driver, blog_data["link"])
        if "오류" in content or "찾을 수 없습니다" in content: continue

        final_state = app_llm_graph.invoke({"original_text": content, "keyword": keyword, "title": blog_data["title"], "log_details": False, "re_summarize_count": 0, "is_relevant": False})

        if not final_state.get("is_relevant"): continue

        judgments = final_state.get("final_judgments", [])
        num_pos = sum(1 for res in judgments if res["final_verdict"] == "긍정")
        num_neg = sum(1 for res in judgments if res["final_verdict"] == "부정")
        num_neu = len(judgments) - num_pos - num_neg
        
        total_pos_sentences += num_pos
        total_neg_sentences += num_neg

        # 부정적인 문장 수집
        for res in judgments:
            if res["final_verdict"] == "부정":
                all_negative_sentences.append(res["sentence"])

        season = get_season(blog_data['postdate'])
        seasonal_data[season]["pos"] += num_pos
        seasonal_data[season]["neg"] += num_neg

        display_sentences = [f"[{res['final_verdict']}] {res['sentence']}" for res in judgments]
        
        results.append({
            "블로그 제목": blog_data["title"],
            "링크": blog_data["link"],
            "긍정 문장 수": num_pos, "부정 문장 수": num_neg, "중립 문장 수": num_neu,
            "긍정 비율 (%)": f"{(num_pos/(num_pos+num_neg)*100):.1f}" if (num_pos+num_neg) > 0 else "0.0",
            "긍/부정 문장 요약": "\n---\n".join(display_sentences),
        })
        valid_blogs_data.append(blog_data)

        if len(valid_blogs_data) >= num_reviews: break

    if not results:
        return {"error": f"'{keyword}'에 대한 유효한 후기 블로그를 찾지 못했습니다."}

    # 부정적 의견 요약 및 CSV 저장
    negative_summary_text = summarize_negative_feedback(all_negative_sentences)
    negative_summary_csv_path = save_negative_summary_to_csv(negative_summary_text, keyword)

    summary_data = []
    for season, data in seasonal_data.items():
        total = data['pos'] + data['neg']
        summary_data.append({
            "구분": f'{season} 시즌', "긍정 문장 수": data['pos'], "부정 문장 수": data['neg'],
            "긍정 비율 (%)": f"{(data['pos']/total*100):.1f}" if total > 0 else "0.0",
            "부정 비율 (%)": f"{(data['neg']/total*100):.1f}" if total > 0 else "0.0",
        })
    total_all = total_pos_sentences + total_neg_sentences
    summary_data.append({
        "구분": "전체 요약", "긍정 문장 수": total_pos_sentences, "부정 문장 수": total_neg_sentences,
        "긍정 비율 (%)": f"{(total_pos_sentences/total_all*100):.1f}" if total_all > 0 else "0.0",
        "부정 비율 (%)": f"{(total_neg_sentences/total_all*100):.1f}" if total_all > 0 else "0.0",
    })
    
    csv_filepath = save_summary_to_csv(summary_data, keyword)
    results_df = pd.DataFrame(results)

    return {
        "status": f"총 {total_searched}개 중 {len(candidate_blogs)}개 후보 확인, {len(valid_blogs_data)}개 블로그 최종 분석 완료.",
        "overall_chart": create_donut_chart(total_pos_sentences, total_neg_sentences, f'{keyword} 전체 후기 요약'),
        "spring_chart": create_stacked_bar_chart(seasonal_data["봄"]["pos"], seasonal_data["봄"]["neg"], "봄 시즌"),
        "summer_chart": create_stacked_bar_chart(seasonal_data["여름"]["pos"], seasonal_data["여름"]["neg"], "여름 시즌"),
        "autumn_chart": create_stacked_bar_chart(seasonal_data["가을"]["pos"], seasonal_data["가을"]["neg"], "가을 시즌"),
        "winter_chart": create_stacked_bar_chart(seasonal_data["겨울"]["pos"], seasonal_data["겨울"]["neg"], "겨울 시즌"),
        "download_file": gr.File(value=csv_filepath, visible=True),
        "results_df": results_df,
        "url_markdown": f"### 분석된 블로그 URL ({len(valid_blogs_data)}개)\n" + "\n".join([f"- [{b['title']}]({b['link']})" for b in valid_blogs_data]),
        "negative_summary_text": negative_summary_text,
        "negative_summary_download_file": gr.File(value=negative_summary_csv_path, visible=negative_summary_csv_path is not None)
    }

def analyze_keyword_and_generate_report(keyword: str, num_reviews: int, progress=gr.Progress(track_tqdm=True)):
    num_reviews = int(num_reviews)
    progress(0, desc="웹 드라이버 설정 중...")
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        results = _perform_analysis(keyword, num_reviews, driver, "분석 중", progress)

        if "error" in results:
            # 15개의 반환 값에 맞춰 빈 값들로 채움
            return [results["error"]] + [gr.update(visible=False)]*14

        initial_page_df, _, total_pages_str = change_page(results["results_df"], 1)

        return (
            results["status"],
            gr.update(value=results["overall_chart"], visible=results["overall_chart"] is not None),
            gr.update(value=results["spring_chart"], visible=results["spring_chart"] is not None),
            gr.update(value=results["summer_chart"], visible=results["summer_chart"] is not None),
            gr.update(value=results["autumn_chart"], visible=results["autumn_chart"] is not None),
            gr.update(value=results["winter_chart"], visible=results["winter_chart"] is not None),
            results["download_file"],
            initial_page_df,
            results["url_markdown"],
            results["results_df"],
            1, 
            total_pages_str,
            gr.update(value=results["negative_summary_text"], visible=bool(results["negative_summary_text"])),
            results["negative_summary_download_file"]
        )
    finally:
        if driver:
            driver.quit()

def run_comparison_analysis(keyword_a: str, keyword_b: str, num_reviews: int, progress=gr.Progress(track_tqdm=True)):
    # 이 함수는 현재 요청 범위에서 제외되었으므로, 간단히 플레이스홀더로 남겨둡니다.
    # 추후 필요시 analyze_keyword_and_generate_report와 유사한 방식으로 수정해야 합니다.
    progress(1, desc="비교 분석 기능은 현재 업데이트 중입니다.")
    return [gr.update()]*28 # 출력 개수에 맞게 빈 업데이트 반환