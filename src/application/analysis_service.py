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

PAGE_SIZE = 10

# --- Helper Functions ---
def change_page(full_df, page_num):
    if not isinstance(full_df, pd.DataFrame) or full_df.empty:
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
    if not sentences: return ""
    llm = get_llm_client(model="gemini-2.5-pro")
    unique_sentences = sorted(list(set(sentences)), key=len, reverse=True)
    negative_feedback_str = "\n- ".join(unique_sentences)
    prompt = f'''[수집된 부정적인 의견]\n- {negative_feedback_str}\n\n[요청] 위 의견들을 종합하여 주요 불만 사항을 1., 2., 3. ... 형식의 목록으로 요약해주세요.'''
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"부정적 의견 요약 중 오류 발생: {e}")
        return "부정적 의견을 요약하는 데 실패했습니다."

def save_negative_summary_to_csv(summary_text: str, keyword: str) -> str:
    if not summary_text or "실패했습니다" in summary_text: return None
    items = re.findall(r"^\d+\.\s*(.*)", summary_text, re.MULTILINE)
    if not items: return None
    df = pd.DataFrame(items, columns=["주요 불만 사항"])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_keyword = re.sub(r'[\\/*?"<>|]', '', keyword)
    csv_filepath = f"{sanitized_keyword}_negative_summary_{timestamp}.csv"
    df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
    return csv_filepath

# --- Core Analysis Logic ---

def _analyze_single_festival(keyword: str, num_reviews: int, driver, log_details: bool) -> dict:
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

    if not candidate_blogs: return {"error": f"'{search_keyword}' 블로그 없음"}

    valid_blogs_data, all_negative_sentences = [], []
    total_pos, total_neg = 0, 0
    seasonal_data = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}}

    for blog_data in candidate_blogs:
        if len(valid_blogs_data) >= num_reviews: break
        content = scrape_blog_content(driver, blog_data["link"])
        if "오류" in content or "찾을 수 없습니다" in content: continue

        final_state = app_llm_graph.invoke({"original_text": content, "keyword": keyword, "title": blog_data["title"], "log_details": log_details, "re_summarize_count": 0, "is_relevant": False})
        if not final_state.get("is_relevant"): continue

        judgments = final_state.get("final_judgments", [])
        pos_count = sum(1 for res in judgments if res["final_verdict"] == "긍정")
        neg_count = sum(1 for res in judgments if res["final_verdict"] == "부정")
        
        total_pos += pos_count
        total_neg += neg_count
        all_negative_sentences.extend([res["sentence"] for res in judgments if res["final_verdict"] == "부정"])
        
        season = get_season(blog_data['postdate'])
        seasonal_data[season]["pos"] += pos_count
        seasonal_data[season]["neg"] += neg_count
        valid_blogs_data.append(blog_data)

    if not valid_blogs_data: return {"error": f"'{keyword}' 유효 리뷰 없음"}

    return {
        "keyword": keyword,
        "total_pos": total_pos,
        "total_neg": total_neg,
        "negative_sentences": all_negative_sentences,
        "seasonal_data": seasonal_data,
        "positive_ratio": f"{(total_pos / (total_pos + total_neg) * 100):.1f}" if (total_pos + total_neg) > 0 else "0.0"
    }

def _perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, progress, initial_progress, total_steps, log_details):
    festivals_to_analyze = festival_loader.get_festivals(cat1, cat2, cat3)
    if not festivals_to_analyze: return {"error": "분석할 축제를 찾을 수 없습니다."}

    category_results = []
    total_festivals = len(festivals_to_analyze)
    for i, festival_name in enumerate(festivals_to_analyze):
        current_step_progress = (i + 1) / total_festivals
        overall_progress = (initial_progress + current_step_progress) / total_steps
        progress(overall_progress, desc=f"분석 중: {festival_name} ({i+1}/{total_festivals})")
        
        result = _analyze_single_festival(festival_name, num_reviews, driver, log_details)
        if "error" not in result:
            category_results.append(result)
    
    if not category_results: return {"error": "모든 축제에 대한 유효한 리뷰를 찾지 못했습니다."}

    # 1. 종합 결과 집계
    agg_pos = sum(r["total_pos"] for r in category_results)
    agg_neg = sum(r["total_neg"] for r in category_results)
    agg_seasonal = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}}
    agg_negative_sentences = []
    for r in category_results:
        agg_negative_sentences.extend(r["negative_sentences"])
        for season, data in r["seasonal_data"].items():
            agg_seasonal[season]["pos"] += data["pos"]
            agg_seasonal[season]["neg"] += data["neg"]

    # 2. 종합 결과물 생성
    category_name = cat3 or cat2 or cat1
    neg_summary_text = summarize_negative_feedback(agg_negative_sentences)
    neg_summary_csv = save_negative_summary_to_csv(neg_summary_text, category_name)
    
    # 3. 개별 축제 결과 테이블 생성
    individual_results_df = pd.DataFrame([{
        "축제명": r["keyword"],
        "긍정 문장 수": r["total_pos"],
        "부정 문장 수": r["total_neg"],
        "긍정 비율 (%)": r["positive_ratio"]
    } for r in category_results])

    status = f"총 {total_festivals}개 중 {len(category_results)}개 축제 분석 완료."
    return {
        "status": status,
        "negative_summary_text": neg_summary_text,
        "negative_summary_download_file": neg_summary_csv,
        "overall_chart": create_donut_chart(agg_pos, agg_neg, f'{category_name} 종합 분석'),
        "spring_chart": create_stacked_bar_chart(agg_seasonal["봄"]["pos"], agg_seasonal["봄"]["neg"], "봄 시즌"),
        "summer_chart": create_stacked_bar_chart(agg_seasonal["여름"]["pos"], agg_seasonal["여름"]["neg"], "여름 시즌"),
        "autumn_chart": create_stacked_bar_chart(agg_seasonal["가을"]["pos"], agg_seasonal["가을"]["neg"], "가을 시즌"),
        "winter_chart": create_stacked_bar_chart(agg_seasonal["겨울"]["pos"], agg_seasonal["겨울"]["neg"], "겨울 시즌"),
        "individual_results_df": individual_results_df
    }

# --- Gradio Service Functions ---
def analyze_festivals_by_category(cat1, cat2, cat3, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    num_reviews = int(num_reviews)
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        results = _perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, progress, 0, 1, log_details)
        
        if "error" in results:
            return [results["error"]] + [gr.update(visible=False)]*11

        initial_page_df, _, total_pages_str = change_page(results["individual_results_df"], 1)

        return (
            results["status"],
            gr.update(value=results["negative_summary_text"], visible=bool(results["negative_summary_text"])),
            gr.update(value=results["negative_summary_download_file"], visible=results["negative_summary_download_file"] is not None),
            gr.update(value=results["overall_chart"], visible=True),
            gr.update(value=results["spring_chart"], visible=results["spring_chart"] is not None),
            gr.update(value=results["summer_chart"], visible=results["summer_chart"] is not None),
            gr.update(value=results["autumn_chart"], visible=results["autumn_chart"] is not None),
            gr.update(value=results["winter_chart"], visible=results["winter_chart"] is not None),
            initial_page_df,
            results["individual_results_df"],
            1, 
            total_pages_str
        )
    finally:
        if driver:
            driver.quit()

def compare_categories(cat1_a, cat2_a, cat3_a, cat1_b, cat2_b, cat3_b, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    num_reviews = int(num_reviews)
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=chrome_options)

        results_a = _perform_category_analysis(cat1_a, cat2_a, cat3_a, num_reviews, driver, progress, 0, 2, log_details)
        results_b = _perform_category_analysis(cat1_b, cat2_b, cat3_b, num_reviews, driver, progress, 1, 2, log_details)

        # UI 반환 값 생성 로직
        def create_output_tuple(res):
            if "error" in res:
                return [res["error"]] + [gr.update(visible=False)]*11
            
            initial_page_df, _, total_pages_str = change_page(res["individual_results_df"], 1)
            return (
                res["status"],
                gr.update(value=res["negative_summary_text"], visible=bool(res["negative_summary_text"])),
                gr.update(value=res["negative_summary_download_file"], visible=res["negative_summary_download_file"] is not None),
                gr.update(value=res["overall_chart"], visible=True),
                gr.update(value=res["spring_chart"], visible=res["spring_chart"] is not None),
                gr.update(value=res["summer_chart"], visible=res["summer_chart"] is not None),
                gr.update(value=res["autumn_chart"], visible=res["autumn_chart"] is not None),
                gr.update(value=res["winter_chart"], visible=res["winter_chart"] is not None),
                initial_page_df,
                res["individual_results_df"],
                1, 
                total_pages_str
            )

        output_a = create_output_tuple(results_a)
        output_b = create_output_tuple(results_b)
        
        return tuple(output_a) + tuple(output_b)
    finally:
        if driver:
            driver.quit()

# --- Legacy Functions (To be restored if needed) ---
def analyze_keyword_and_generate_report(keyword: str, num_reviews: int, progress=gr.Progress(track_tqdm=True)):
    # This function can be restored using a similar pattern to analyze_festivals_by_category
    return ["This function is currently disabled."] + [gr.update(visible=False)]*13

def run_comparison_analysis(keyword_a: str, keyword_b: str, num_reviews: int, progress=gr.Progress(track_tqdm=True)):
    return [gr.update()]*28