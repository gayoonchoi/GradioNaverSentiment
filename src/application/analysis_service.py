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

def save_df_to_csv(df: pd.DataFrame, base_name: str, keyword: str) -> str:
    if df is None or df.empty: return None
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sanitized_keyword = re.sub(r'[\\/*?"<>|]', '', keyword)
    csv_filepath = f"{sanitized_keyword}_{base_name}_{timestamp}.csv"
    df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
    return csv_filepath

def summarize_negative_feedback(sentences: list) -> str:
    if not sentences: return ""
    llm = get_llm_client(model="gemini-2.5-pro")
    unique_sentences = sorted(list(set(sentences)), key=len, reverse=True)
    # LLM 부하를 줄이기 위해 최대 50개 문장만 요약 대상으로 함
    negative_feedback_str = "\n- ".join(unique_sentences[:50]) 
    prompt = f'''[수집된 부정적인 의견]\n- {negative_feedback_str}\n\n[요청] 위 의견들을 종합하여 주요 불만 사항을 1., 2., 3. ... 형식의 목록으로 요약해주세요.'''
    try:
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"부정적 의견 요약 중 오류 발생: {e}")
        return "부정적 의견을 요약하는 데 실패했습니다."

# --- Core Analysis Logic ---
def _analyze_single_keyword_fully(keyword: str, num_reviews: int, driver, log_details: bool, progress: gr.Progress, progress_desc: str):
    search_keyword = f"{keyword} 후기"
    max_candidates = max(50, num_reviews * 8)
    candidate_blogs, blog_results_list, all_negative_sentences = [], [], []
    blog_judgments_list = []
    total_pos, total_neg, total_searched, start_index = 0, 0, 0, 1
    total_strong_pos, total_strong_neg = 0, 0
    seasonal_data = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}}
    
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

    if not candidate_blogs: return {"error": f"'{search_keyword}'에 대한 네이버 블로그를 찾을 수 없습니다."}

    valid_blogs_data = []
    for i, blog_data in enumerate(candidate_blogs):
        if len(valid_blogs_data) >= num_reviews: break
        progress((i + 1) / len(candidate_blogs), desc=f"[{progress_desc}] {keyword} 분석 중... ({len(valid_blogs_data)}/{num_reviews} 완료)")
        content = scrape_blog_content(driver, blog_data["link"])
        if "오류" in content or "찾을 수 없습니다" in content: continue

        final_state = app_llm_graph.invoke({"original_text": content, "keyword": keyword, "title": blog_data["title"], "log_details": log_details, "re_summarize_count": 0, "is_relevant": False})
        if not final_state.get("is_relevant"): continue

        judgments = final_state.get("final_judgments", [])
        blog_judgments_list.append(judgments)
        pos_count = sum(1 for res in judgments if res["final_verdict"] == "긍정")
        neg_count = sum(1 for res in judgments if res["final_verdict"] == "부정")
        
        strong_pos_count = sum(1 for res in judgments if res["final_verdict"] == "긍정" and res["score"] >= 1.0)
        strong_neg_count = sum(1 for res in judgments if res["final_verdict"] == "부정" and res["score"] < -1.0)

        total_pos += pos_count
        total_neg += neg_count
        total_strong_pos += strong_pos_count
        total_strong_neg += strong_neg_count
        all_negative_sentences.extend([res["sentence"] for res in judgments if res["final_verdict"] == "부정"])
        
        season = get_season(blog_data['postdate'])
        seasonal_data[season]["pos"] += pos_count
        seasonal_data[season]["neg"] += neg_count
        
        sentiment_frequency = pos_count + neg_count
        sentiment_score = ((strong_pos_count + strong_neg_count) / sentiment_frequency * 100) if sentiment_frequency > 0 else 0

        blog_results_list.append({
            "블로그 제목": blog_data["title"], "링크": blog_data["link"], 
            "감성 빈도": sentiment_frequency, "감성 점수": f"{sentiment_score:.1f}",
            "긍정 문장 수": pos_count, "부정 문장 수": neg_count,
            "긍정 비율 (%)": f"{(pos_count/sentiment_frequency*100):.1f}" if sentiment_frequency > 0 else "0.0",
            "부정 비율 (%)": f"{(neg_count/sentiment_frequency*100):.1f}" if sentiment_frequency > 0 else "0.0",
            "긍/부정 문장 요약": "\n---\n".join([f"[{res['final_verdict']}] {res['sentence']}" for res in judgments])
        })
        valid_blogs_data.append(blog_data)

    if not valid_blogs_data: return {"error": f"'{keyword}'에 대한 유효한 후기 블로그를 찾지 못했습니다."}

    total_sentiment_frequency = total_pos + total_neg
    total_sentiment_score = ((total_strong_pos + total_strong_neg) / total_sentiment_frequency * 100) if total_sentiment_frequency > 0 else 0

    return {
        "status": f"총 {total_searched}개 중 {len(candidate_blogs)}개 후보 확인, {len(valid_blogs_data)}개 블로그 최종 분석 완료.",
        "total_pos": total_pos, "total_neg": total_neg, 
        "total_strong_pos": total_strong_pos, "total_strong_neg": total_strong_neg,
        "total_sentiment_frequency": total_sentiment_frequency,
        "total_sentiment_score": total_sentiment_score,
        "seasonal_data": seasonal_data,
        "negative_sentences": all_negative_sentences, 
        "blog_results_df": pd.DataFrame(blog_results_list),
        "blog_judgments": blog_judgments_list,
        "url_markdown": f"### 분석된 블로그 URL ({len(valid_blogs_data)}개)\n" + "\n".join([f"- [{b['title']}]({b['link']})" for b in valid_blogs_data])
    }

# [수정] 각 축제 분석 후 즉시 요약하고 결과를 저장하도록 변경
def _perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, log_details, progress, initial_progress, total_steps):
    festivals_to_analyze = festival_loader.get_festivals(cat1, cat2, cat3)
    if not festivals_to_analyze: return {"error": "분석할 축제를 찾을 수 없습니다."}

    category_results, all_blog_posts_list = [], []
    festival_full_results = []
    agg_pos, agg_neg = 0, 0
    agg_strong_pos, agg_strong_neg = 0, 0
    agg_seasonal = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}}
    agg_negative_sentences = []

    total_festivals = len(festivals_to_analyze)
    for i, festival_name in enumerate(festivals_to_analyze):
        # 진행률 업데이트 로직 개선
        current_festival_progress = (i) / total_festivals
        overall_progress = (initial_progress + current_festival_progress) / total_steps
        
        # 각 축제 내 블로그 분석 진행률 표시를 위한 nested progress
        def nested_progress_callback(p, desc=""):
             # 각 축제는 전체 진행률의 1/total_festivals 만큼 기여
            festival_step_progress = p / total_festivals 
            current_overall_progress = overall_progress + festival_step_progress
            progress(current_overall_progress, desc=f"분석 중: {festival_name} ({i+1}/{total_festivals}) - {desc}")

        result = _analyze_single_keyword_fully(festival_name, num_reviews, driver, log_details, nested_progress_callback, "블로그 분석")
        if "error" in result: continue

        # --- 핵심 수정: 각 축제 분석 직후 요약 실행 ---
        print(f"   [{festival_name}] 부정 문장 요약 시작...")
        neg_summary = summarize_negative_feedback(result["negative_sentences"])
        result['precomputed_negative_summary'] = neg_summary # 전체 결과에도 저장 (UI 클릭 시 사용)
        print(f"   [{festival_name}] 부정 문장 요약 완료.")
        # ----------------------------------------------
        
        festival_full_results.append(result)

        agg_pos += result["total_pos"]
        agg_neg += result["total_neg"]
        agg_strong_pos += result.get("total_strong_pos", 0)
        agg_strong_neg += result.get("total_strong_neg", 0)
        agg_negative_sentences.extend(result["negative_sentences"])
        for season, data in result["seasonal_data"].items():
            agg_seasonal[season]["pos"] += data["pos"]
            agg_seasonal[season]["neg"] += data["neg"]
        
        # --- 핵심 수정: category_results에 모든 정보 추가 (CSV용) ---
        total_freq = result["total_pos"] + result["total_neg"]
        pos_perc = (result['total_pos'] / total_freq * 100) if total_freq > 0 else 0.0
        neg_perc = (result['total_neg'] / total_freq * 100) if total_freq > 0 else 0.0
        
        category_results.append({
            "축제명": festival_name,
            '감성 빈도': result['total_sentiment_frequency'],
            '감성 점수': f"{result['total_sentiment_score']:.1f}",
            "긍정 문장 수": result["total_pos"],
            "부정 문장 수": result["total_neg"],
            "긍정 비율 (%)": f"{pos_perc:.1f}",
            "부정 비율 (%)": f"{neg_perc:.1f}", 
            '주요 불만 사항 요약': neg_summary 
        })
        # ----------------------------------------------------

        if not result["blog_results_df"].empty:
            all_blog_posts_list.append(result["blog_results_df"])

    if not category_results: return {"error": "모든 축제에 대한 유효한 리뷰를 찾지 못했습니다."}

    total_sentiment_frequency = agg_pos + agg_neg
    total_sentiment_score = ((agg_strong_pos + agg_strong_neg) / total_sentiment_frequency * 100) if total_sentiment_frequency > 0 else 0

    all_blog_judgments = []
    for res in festival_full_results:
        all_blog_judgments.extend(res.get("blog_judgments", []))

    return {
        "status": f"총 {total_festivals}개 중 {len(category_results)}개 축제 분석 완료.",
        "total_pos": agg_pos, "total_neg": agg_neg, 
        "total_sentiment_frequency": total_sentiment_frequency,
        "total_sentiment_score": total_sentiment_score,
        "seasonal_data": agg_seasonal,
        "negative_sentences": agg_negative_sentences,
        "individual_festival_results_df": pd.DataFrame(category_results), # 풍부해진 데이터 사용
        "all_blog_posts_df": pd.concat(all_blog_posts_list, ignore_index=True) if all_blog_posts_list else pd.DataFrame(),
        "festival_full_results": festival_full_results, # 요약 포함된 결과 사용
        "all_blog_judgments": all_blog_judgments
    }

# --- Gradio Service Functions ---
def _create_driver():
    service = Service(ChromeDriverManager().install())
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    return webdriver.Chrome(service=service, options=chrome_options)

def _package_keyword_results(results: dict, name: str):
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * 19

    neg_summary_text = summarize_negative_feedback(results["negative_sentences"])
    overall_summary_text = f"""
- **긍정 문장 수**: {results['total_pos']}개
- **부정 문장 수**: {results['total_neg']}개
- **감성어 빈도 (긍정+부정)**: {results['total_sentiment_frequency']}개
- **감성 점수**: {results['total_sentiment_score']:.1f}점"""

    summary_df = pd.DataFrame([{
        '검색어': name,
        '감성 빈도': results['total_sentiment_frequency'],
        '감성 점수': f"{results['total_sentiment_score']:.1f}",
        '긍정 문장 수': results["total_pos"], 
        '부정 문장 수': results["total_neg"],
        '긍정 비율 (%)': f"{(results['total_pos'] / results['total_sentiment_frequency'] * 100):.1f}" if results['total_sentiment_frequency'] > 0 else "0.0",
        '부정 비율 (%)': f"{(results['total_neg'] / results['total_sentiment_frequency'] * 100):.1f}" if results['total_sentiment_frequency'] > 0 else "0.0",
        '주요 불만 사항 요약': neg_summary_text
    }])
    summary_csv = save_df_to_csv(summary_df, "overall_summary", name)

    blog_df_for_csv = results["blog_results_df"].copy()
    blog_df_for_csv['긍/부정 문장 요약'] = blog_df_for_csv['긍/부정 문장 요약'].str.slice(0, 50) + '...더보기'
    blog_list_csv = save_df_to_csv(blog_df_for_csv, "blog_list", name)

    df_for_display = results["blog_results_df"].drop(columns=['긍/부정 문장 요약'])
    initial_page_df, _, total_pages_str = change_page(df_for_display, 1)

    return (
        results["status"],
        results["url_markdown"],
        gr.update(value=neg_summary_text, visible=bool(neg_summary_text)),
        gr.update(value=create_donut_chart(results["total_pos"], results["total_neg"], f'{name} 전체 후기 요약'), visible=True),
        gr.update(value=overall_summary_text, visible=True),
        gr.update(value=summary_csv, visible=summary_csv is not None),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["봄"]["pos"], results["seasonal_data"]["봄"]["neg"], "봄 시즌"), visible=results["seasonal_data"]["봄"]["pos"] > 0 or results["seasonal_data"]["봄"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["여름"]["pos"], results["seasonal_data"]["여름"]["neg"], "여름 시즌"), visible=results["seasonal_data"]["여름"]["pos"] > 0 or results["seasonal_data"]["여름"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["가을"]["pos"], results["seasonal_data"]["가을"]["neg"], "가을 시즌"), visible=results["seasonal_data"]["가을"]["pos"] > 0 or results["seasonal_data"]["가을"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["겨울"]["pos"], results["seasonal_data"]["겨울"]["neg"], "겨울 시즌"), visible=results["seasonal_data"]["겨울"]["pos"] > 0 or results["seasonal_data"]["겨울"]["neg"] > 0),
        initial_page_df,
        results["blog_results_df"],
        results["blog_judgments"],
        1,
        total_pages_str,
        gr.update(value=blog_list_csv, visible=blog_list_csv is not None),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False)
    )

# [수정] 클릭 시 LLM 호출 대신 미리 계산된 요약 사용
def package_festival_details(results: dict, name: str):
    if "error" in results:
        return [gr.update(value=results["error"], visible=True)] + [gr.update(visible=False)] * 7

    # --- 핵심 수정: 미리 계산된 요약 결과 사용 ---
    neg_summary_text = results.get("precomputed_negative_summary", "미리 계산된 요약 없음") 
    # ---------------------------------------------

    overall_summary_text = f"""
- **긍정 문장 수**: {results['total_pos']}개
- **부정 문장 수**: {results['total_neg']}개
- **감성어 빈도 (긍정+부정)**: {results['total_sentiment_frequency']}개
- **감성 점수**: {results['total_sentiment_score']:.1f}점"""

    return [
        gr.update(value=neg_summary_text, visible=bool(neg_summary_text)),
        gr.update(value=create_donut_chart(results["total_pos"], results["total_neg"], f'{name} 후기 요약'), visible=True),
        gr.update(value=overall_summary_text, visible=True),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["봄"]["pos"], results["seasonal_data"]["봄"]["neg"], "봄 시즌"), visible=results["seasonal_data"]["봄"]["pos"] > 0 or results["seasonal_data"]["봄"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["여름"]["pos"], results["seasonal_data"]["여름"]["neg"], "여름 시즌"), visible=results["seasonal_data"]["여름"]["pos"] > 0 or results["seasonal_data"]["여름"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["가을"]["pos"], results["seasonal_data"]["가을"]["neg"], "가을 시즌"), visible=results["seasonal_data"]["가을"]["pos"] > 0 or results["seasonal_data"]["가을"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["겨울"]["pos"], results["seasonal_data"]["겨울"]["neg"], "겨울 시즌"), visible=results["seasonal_data"]["겨울"]["pos"] > 0 or results["seasonal_data"]["겨울"]["neg"] > 0),
        gr.update(visible=True, open=True) 
    ]

# [수정] CSV 저장 시 풍부해진 DataFrame을 사용
def _package_category_results(results: dict, name: str):
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * 33

    cat_neg_summary_text = summarize_negative_feedback(results["negative_sentences"])
    cat_overall_summary_text = f"""
- **긍정 문장 수**: {results['total_pos']}개
- **부정 문장 수**: {results['total_neg']}개
- **감성어 빈도 (긍정+부정)**: {results['total_sentiment_frequency']}개
- **감성 점수**: {results['total_sentiment_score']:.1f}점"""
    
    summary_df = pd.DataFrame([{
        '카테고리': name,
        '감성 빈도': results['total_sentiment_frequency'],
        '감성 점수': f"{results['total_sentiment_score']:.1f}",
        '긍정 문장 수': results["total_pos"], 
        '부정 문장 수': results["total_neg"],
        '긍정 비율 (%)': f"{(results['total_pos'] / results['total_sentiment_frequency'] * 100):.1f}" if results['total_sentiment_frequency'] > 0 else "0.0",
        '부정 비율 (%)': f"{(results['total_neg'] / results['total_sentiment_frequency'] * 100):.1f}" if results['total_sentiment_frequency'] > 0 else "0.0",
        '주요 불만 사항 요약': cat_neg_summary_text
    }])
    cat_overall_csv = save_df_to_csv(summary_df, "category_summary", name)

    # --- 핵심 수정: 풍부해진 individual_festival_results_df 사용 ---
    festival_df_for_csv = results["individual_festival_results_df"].copy()
    festival_list_csv = save_df_to_csv(festival_df_for_csv, "festival_summary", name)
    # -----------------------------------------------------------
    
    festival_page_df, _, festival_pages_str = change_page(results["individual_festival_results_df"], 1)

    all_blogs_df = results["all_blog_posts_df"]
    blog_df_for_csv = all_blogs_df.copy()
    if not blog_df_for_csv.empty:
        # CSV 저장 시 요약 내용 축약 (기존과 동일)
        blog_df_for_csv['긍/부정 문장 요약'] = blog_df_for_csv['긍/부정 문장 요약'].str.slice(0, 50) + '...더보기'
    all_blogs_list_csv = save_df_to_csv(blog_df_for_csv, "all_blogs", name)
    
    # UI 표시용 DataFrame에서는 요약 열 제거 (기존과 동일)
    df_for_display = all_blogs_df.drop(columns=['긍/부정 문장 요약']) if not all_blogs_df.empty else all_blogs_df
    blog_page_df, _, blog_pages_str = change_page(df_for_display, 1)

    return (
        results["status"],
        gr.update(value=cat_neg_summary_text, visible=bool(cat_neg_summary_text)),
        gr.update(value=create_donut_chart(results["total_pos"], results["total_neg"], f'{name} 종합 분석'), visible=True),
        gr.update(value=cat_overall_summary_text, visible=True),
        gr.update(value=cat_overall_csv, visible=cat_overall_csv is not None),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["봄"]["pos"], results["seasonal_data"]["봄"]["neg"], "봄 시즌"), visible=results["seasonal_data"]["봄"]["pos"] > 0 or results["seasonal_data"]["봄"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["여름"]["pos"], results["seasonal_data"]["여름"]["neg"], "여름 시즌"), visible=results["seasonal_data"]["여름"]["pos"] > 0 or results["seasonal_data"]["여름"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["가을"]["pos"], results["seasonal_data"]["가을"]["neg"], "가을 시즌"), visible=results["seasonal_data"]["가을"]["pos"] > 0 or results["seasonal_data"]["가을"]["neg"] > 0),
        gr.update(value=create_stacked_bar_chart(results["seasonal_data"]["겨울"]["pos"], results["seasonal_data"]["겨울"]["neg"], "겨울 시즌"), visible=results["seasonal_data"]["겨울"]["pos"] > 0 or results["seasonal_data"]["겨울"]["neg"] > 0),
        festival_page_df,
        results["individual_festival_results_df"], # State용 (풍부해진 데이터)
        results["festival_full_results"], # State용 (요약 포함된 데이터)
        1,
        festival_pages_str,
        gr.update(value=festival_list_csv, visible=festival_list_csv is not None),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
        blog_page_df,
        all_blogs_df,
        results["all_blog_judgments"],
        1,
        blog_pages_str,
        gr.update(value=all_blogs_list_csv, visible=all_blogs_list_csv is not None),
        gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)
    )

def analyze_keyword_and_generate_report(keyword: str, num_reviews: int, log_details: bool, progress=gr.Progress(track_tqdm=True)):
    driver = None
    try:
        driver = _create_driver()
        results = _analyze_single_keyword_fully(keyword, int(num_reviews), driver, log_details, progress, "단일 분석")
        return _package_keyword_results(results, keyword)
    finally:
        if driver: driver.quit()

def run_comparison_analysis(keyword_a: str, keyword_b: str, num_reviews: int, log_details: bool, progress=gr.Progress(track_tqdm=True)):
    driver = None
    try:
        driver = _create_driver()
        results_a = _analyze_single_keyword_fully(keyword_a, int(num_reviews), driver, log_details, progress, "비교(A)")
        results_b = _analyze_single_keyword_fully(keyword_b, int(num_reviews), driver, log_details, progress, "비교(B)")
        output_a = _package_keyword_results(results_a, keyword_a)
        output_b = _package_keyword_results(results_b, keyword_b)
        return tuple(output_a) + tuple(output_b)
    finally:
        if driver: driver.quit()

def analyze_festivals_by_category(cat1, cat2, cat3, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    driver = None
    try:
        driver = _create_driver()
        results = _perform_category_analysis(cat1, cat2, cat3, int(num_reviews), driver, log_details, progress, 0, 1)
        return _package_category_results(results, cat3 or cat2 or cat1)
    finally:
        if driver: driver.quit()

def compare_categories(cat1_a, cat2_a, cat3_a, cat1_b, cat2_b, cat3_b, num_reviews, log_details, progress=gr.Progress(track_tqdm=True)):
    driver = None
    try:
        driver = _create_driver()
        results_a = _perform_category_analysis(cat1_a, cat2_a, cat3_a, int(num_reviews), driver, log_details, progress, 0, 2)
        results_b = _perform_category_analysis(cat1_b, cat2_b, cat3_b, int(num_reviews), driver, log_details, progress, 1, 2)
        output_a = _package_category_results(results_a, cat3_a or cat2_a or cat1_a)
        output_b = _package_category_results(results_b, cat3_b or cat2_b or cat1_b)
        return tuple(output_a) + tuple(output_b)
    finally:
        if driver: driver.quit()