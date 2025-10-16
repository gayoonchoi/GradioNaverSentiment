
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
from src.data import festival_loader
from src.infrastructure.reporting.composite_chart import create_composite_image

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
    if not sentences:
        return ""
    llm = get_llm_client(model="gemini-2.5-pro")
    unique_sentences = sorted(list(set(sentences)), key=len, reverse=True)
    negative_feedback_str = "\n- ".join(unique_sentences)
    prompt = f'''
    아래는 서비스/장소에 대한 여러 블로그 리뷰에서 수집된 부정적인 의견들입니다. 
    이 의견들을 종합하여 사용자가 겪은 주요 불만 사항들을 1., 2., 3. ... 형식의 목록으로 요약해주세요.
    - 비슷한 내용의 의견은 하나로 묶어서 대표적인 불만 사항으로 만들어주세요.
    - 각 항목은 사용자가 어떤 점을 왜 부정적으로 느꼈는지 명확히 드러나도록 간결하게 작성해주세요.
    - 최소 3개, 최대 10개의 주요 불만 사항으로 요약해주세요.

    [수집된 부정적인 의견]
    - {negative_feedback_str}

    [주요 불만 사항 요약]
    '''
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"부정적 의견 요약 중 오류 발생: {e}")
        return "부정적 의견을 요약하는 데 실패했습니다."

def save_negative_summary_to_csv(summary_text: str, keyword: str) -> str:
    if not summary_text or "실패했습니다" in summary_text:
        return None
    items = re.findall(r"^\d+\.\s*(.*)", summary_text, re.MULTILINE)
    if not items:
        return None
    df = pd.DataFrame(items, columns=["주요 불만 사항"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_keyword = re.sub(r'[\\/*?"<>|]', '', keyword)
    csv_filepath = f"{sanitized_keyword}_negative_summary_{timestamp}.csv"
    df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
    return csv_filepath

def _analyze_single_festival(keyword: str, num_reviews: int, driver) -> dict:
    search_keyword = f"{keyword} 후기"
    max_candidates = max(20, num_reviews * 5)
    candidate_blogs = []
    start_index = 1
    while len(candidate_blogs) < max_candidates and start_index <= 201:
        api_results = search_naver_blog_page(search_keyword, start_index=start_index)
        if not api_results: break
        for item in api_results:
            if "blog.naver.com" in item["link"]:
                item['title'] = re.sub(r'<[^>]+>', '', item['title'])
                candidate_blogs.append(item)
                if len(candidate_blogs) >= max_candidates: break
        start_index += 100

    if not candidate_blogs:
        return {"error": f"'{search_keyword}'에 대한 블로그를 찾을 수 없습니다."}

    valid_blogs_data, all_negative_sentences = [], []
    total_pos_sentences, total_neg_sentences = 0, 0
    
    for i, blog_data in enumerate(candidate_blogs):
        if len(valid_blogs_data) >= num_reviews: break
        content = scrape_blog_content(driver, blog_data["link"])
        if "오류" in content or "찾을 수 없습니다" in content: continue

        final_state = app_llm_graph.invoke({"original_text": content, "keyword": keyword, "title": blog_data["title"], "log_details": False, "re_summarize_count": 0, "is_relevant": False})

        if not final_state.get("is_relevant"): continue

        judgments = final_state.get("final_judgments", [])
        pos_count = sum(1 for res in judgments if res["final_verdict"] == "긍정")
        neg_count = sum(1 for res in judgments if res["final_verdict"] == "부정")
        
        total_pos_sentences += pos_count
        total_neg_sentences += neg_count
        all_negative_sentences.extend([res["sentence"] for res in judgments if res["final_verdict"] == "부정"])
        valid_blogs_data.append(blog_data)

    if not valid_blogs_data:
        return {"error": f"'{keyword}'에 대한 유효한 후기를 찾지 못했습니다."}

    return {
        "keyword": keyword,
        "total_pos": total_pos_sentences,
        "total_neg": total_neg_sentences,
        "negative_sentences": all_negative_sentences,
        "chart": create_stacked_bar_chart(total_pos_sentences, total_neg_sentences, keyword)
    }

def _perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, progress, initial_progress, total_steps):
    festivals_to_analyze = festival_loader.get_festivals(cat1, cat2, cat3)
    if not festivals_to_analyze:
        return {"error": "분석할 축제를 찾을 수 없습니다."}

    all_results = []
    total_festivals = len(festivals_to_analyze)
    for i, festival_name in enumerate(festivals_to_analyze):
        current_step_progress = (i + 1) / total_festivals
        overall_progress = (initial_progress + current_step_progress) / total_steps
        progress(overall_progress, desc=f"그룹 분석 중: {festival_name} ({i+1}/{total_festivals})")
        
        result = _analyze_single_festival(festival_name, num_reviews, driver)
        if "error" not in result:
            all_results.append(result)
    
    if not all_results:
        return {"error": "모든 축제에 대한 유효한 리뷰를 찾지 못했습니다."}

    combined_pos = sum(r["total_pos"] for r in all_results)
    combined_neg = sum(r["total_neg"] for r in all_results)
    individual_charts = [r["chart"] for r in all_results if r["chart"] is not None]

    combined_chart = create_donut_chart(combined_pos, combined_neg, "카테고리 종합 분석")
    individual_charts_image = create_composite_image(individual_charts, "축제별 개별 분석 결과")

    status = f"총 {total_festivals}개 중 {len(all_results)}개 축제 분석 완료."
    return {
        "status": status,
        "combined_chart": combined_chart,
        "individual_charts_image": individual_charts_image
    }

def analyze_festivals_by_category(cat1, cat2, cat3, num_reviews, progress=gr.Progress(track_tqdm=True)):
    num_reviews = int(num_reviews)
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        results = _perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, progress, 0, 1)
        if "error" in results:
            return results["error"], None, None
        return results["status"], results["combined_chart"], results["individual_charts_image"]
    finally:
        if driver:
            driver.quit()

def compare_categories(cat1_a, cat2_a, cat3_a, cat1_b, cat2_b, cat3_b, num_reviews, progress=gr.Progress(track_tqdm=True)):
    num_reviews = int(num_reviews)
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        results_a = _perform_category_analysis(cat1_a, cat2_a, cat3_a, num_reviews, driver, progress, 0, 2)
        results_b = _perform_category_analysis(cat1_b, cat2_b, cat3_b, num_reviews, driver, progress, 1, 2)

        output_a = [results_a["status"], results_a["combined_chart"], results_a["individual_charts_image"]] if "error" not in results_a else [results_a["error"], None, None]
        output_b = [results_b["status"], results_b["combined_chart"], results_b["individual_charts_image"]] if "error" not in results_b else [results_b["error"], None, None]
        
        return tuple(output_a + output_b)
    finally:
        if driver:
            driver.quit()

# --- 기존 단일/비교 분석 함수 (현재 비활성화) ---
def analyze_keyword_and_generate_report(keyword: str, num_reviews: int, progress=gr.Progress(track_tqdm=True)):
    return ["이 기능은 현재 비활성화 상태입니다. 카테고리별 분석을 이용해주세요."] + [gr.update(visible=False)]*13

def run_comparison_analysis(keyword_a: str, keyword_b: str, num_reviews: int, progress=gr.Progress(track_tqdm=True)):
    return [gr.update()]*28
