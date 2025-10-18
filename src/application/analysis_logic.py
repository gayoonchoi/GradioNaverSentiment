# src/application/analysis_logic.py
import pandas as pd
import re
import traceback
import gradio as gr # Progress 타입 힌트용
from .utils import get_season # 상대 경로 임포트
from ..application.graph import app_llm_graph
from ..infrastructure.web.naver_api import search_naver_blog_page
from ..infrastructure.web.scraper import scrape_blog_content
from ..data import festival_loader
from .utils import summarize_negative_feedback # 요약 함수 임포트
from ..infrastructure.web.naver_trend_api import create_trend_graph

def analyze_single_keyword_fully(keyword: str, num_reviews: int, driver, log_details: bool, progress: gr.Progress, progress_desc: str):
    """단일 키워드에 대한 전체 분석 수행"""
    search_keyword = f"{keyword} 후기"
    max_candidates = max(50, num_reviews * 10) # 후보 수 증가
    candidate_blogs, blog_results_list, all_negative_sentences = [], [], []
    blog_judgments_list = []
    total_pos, total_neg, total_searched, start_index = 0, 0, 0, 1
    total_strong_pos, total_strong_neg = 0, 0
    seasonal_data = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}, "정보없음": {"pos": 0, "neg": 0}}

    # --- 블로그 후보 수집 ---
    try:
        max_api_calls = 10
        for call_num in range(max_api_calls):
            if len(candidate_blogs) >= max_candidates: break
            call_progress = (call_num + 1) / max_api_calls * 0.2
            progress(call_progress, desc=f"[{progress_desc}] {keyword} 블로그 후보 수집 중... ({len(candidate_blogs)}/{max_candidates})")
            
            api_results = search_naver_blog_page(search_keyword, start_index=start_index)
            if not api_results: break
            total_searched += len(api_results)
            for item in api_results:
                if "blog.naver.com" in item["link"]:
                    item['title'] = re.sub(r'<[^>]+>', '', item['title']).strip()
                    if item['title'] and item["link"]:
                         candidate_blogs.append(item)
                    if len(candidate_blogs) >= max_candidates: break
            start_index += 100
            if start_index > 901: break
    except Exception as e:
        print(f"블로그 후보 수집 중 오류 ({keyword}): {e}")
        traceback.print_exc()
        return {"error": f"'{search_keyword}' 블로그 후보 수집 중 오류 발생"}

    if not candidate_blogs: return {"error": f"'{search_keyword}'에 대한 네이버 블로그를 찾을 수 없습니다."}

    # --- 블로그 분석 ---
    valid_blogs_data = []
    num_candidates_to_process = len(candidate_blogs)
    initial_progress = 0.2
    
    for i, blog_data in enumerate(candidate_blogs):
        if len(valid_blogs_data) >= num_reviews: break
        analysis_progress = (i + 1) / num_candidates_to_process * 0.8
        current_overall_progress = initial_progress + analysis_progress
        progress(min(current_overall_progress, 1.0), desc=f"[{progress_desc}] {keyword} 분석 중... ({len(valid_blogs_data)}/{num_reviews} 완료, {i+1}/{num_candidates_to_process} 확인)")

        try:
            content = scrape_blog_content(driver, blog_data["link"])
            if not content or "오류" in content or "찾을 수 없습니다" in content: continue

            max_content_length = 30000
            if len(content) > max_content_length:
                content = content[:max_content_length] + "... (내용 일부 생략)"

            final_state = app_llm_graph.invoke({
                "original_text": content, "keyword": keyword, "title": blog_data["title"], 
                "log_details": log_details, "re_summarize_count": 0, "is_relevant": False
            })

            if not final_state or not final_state.get("is_relevant"): continue

            judgments = final_state.get("final_judgments", [])
            if not judgments: continue

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
            
            season = get_season(blog_data.get('postdate', ''))
            seasonal_data[season]["pos"] += pos_count
            seasonal_data[season]["neg"] += neg_count
            
            sentiment_frequency = pos_count + neg_count
            sentiment_score = ((strong_pos_count - strong_neg_count) / sentiment_frequency * 50 + 50) if sentiment_frequency > 0 else 50.0
            pos_perc = (pos_count/sentiment_frequency*100) if sentiment_frequency > 0 else 0.0
            neg_perc = (neg_count/sentiment_frequency*100) if sentiment_frequency > 0 else 0.0

            blog_results_list.append({
                "블로그 제목": blog_data["title"], "링크": blog_data["link"], "감성 빈도": sentiment_frequency, 
                "감성 점수": f"{sentiment_score:.1f}", "긍정 문장 수": pos_count, "부정 문장 수": neg_count,
                "긍정 비율 (%)": f"{pos_perc:.1f}", "부정 비율 (%)": f"{neg_perc:.1f}",
                "긍/부정 문장 요약": "\n---\n".join([f"[{res['final_verdict']}] {res['sentence']}" for res in judgments])
            })
            valid_blogs_data.append(blog_data)
        except Exception as e:
            print(f"블로그 분석 중 오류 ({keyword}, {blog_data.get('link', 'N/A')}): {e}")
            traceback.print_exc()
            continue

    if not valid_blogs_data: return {"error": f"'{keyword}'에 대한 유효한 후기 블로그를 찾지 못했습니다 (후보 {len(candidate_blogs)}개 확인)."}

    total_sentiment_frequency = total_pos + total_neg
    total_sentiment_score = ((total_strong_pos - total_strong_neg) / total_sentiment_frequency * 50 + 50) if total_sentiment_frequency > 0 else 50.0

    return {
        "status": f"총 {total_searched}개 검색, {len(candidate_blogs)}개 후보 중 {len(valid_blogs_data)}개 블로그 최종 분석 완료.",
        "total_pos": total_pos, "total_neg": total_neg, "total_strong_pos": total_strong_pos, "total_strong_neg": total_strong_neg,
        "total_sentiment_frequency": total_sentiment_frequency, "total_sentiment_score": total_sentiment_score,
        "seasonal_data": seasonal_data, "negative_sentences": all_negative_sentences, 
        "blog_results_df": pd.DataFrame(blog_results_list) if blog_results_list else pd.DataFrame(),
        "blog_judgments": blog_judgments_list,
        "url_markdown": f"### 분석된 블로그 URL ({len(valid_blogs_data)}개)\n" + "\n".join([f"- [{b['title']}]({b['link']})" for b in valid_blogs_data]),
        "trend_graph": create_trend_graph(keyword)
    }

def perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, log_details, progress: gr.Progress, initial_progress, total_steps):
    """카테고리 내 모든 축제 분석 수행"""
    festivals_to_analyze = festival_loader.get_festivals(cat1, cat2, cat3)
    category_name = cat3 or cat2 or cat1 # 카테고리 이름 저장
    if not festivals_to_analyze: return {"error": f"'{category_name}' 카테고리에서 분석할 축제를 찾을 수 없습니다."}

    category_results, all_blog_posts_list = [], []
    festival_full_results = []
    agg_pos, agg_neg = 0, 0
    agg_strong_pos, agg_strong_neg = 0, 0
    agg_seasonal = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}, "정보없음": {"pos": 0, "neg": 0}}
    agg_negative_sentences = []

    total_festivals = len(festivals_to_analyze)
    for i, festival_name in enumerate(festivals_to_analyze):
        current_festival_progress_base = i / total_festivals
        overall_progress_base = (initial_progress + current_festival_progress_base) / total_steps

        def nested_progress_callback(p, desc=""):
            festival_step_progress = p / total_festivals / total_steps
            current_overall_progress = overall_progress_base + festival_step_progress
            progress(min(current_overall_progress, 1.0), desc=f"분석 중: {festival_name} ({i+1}/{total_festivals}) - {desc}")

        result = analyze_single_keyword_fully(festival_name, num_reviews, driver, log_details, nested_progress_callback, "카테고리 분석")
        
        if "error" in result: 
            print(f"   [{festival_name}] 분석 중 오류 발생: {result['error']}")
            continue
        if result.get("blog_results_df", pd.DataFrame()).empty:
             print(f"   [{festival_name}] 유효한 블로그 분석 결과 없음.")
             continue 

        # --- 미리 요약 수행 ---
        print(f"   [{festival_name}] 부정 문장 요약 시작...")
        neg_summary = summarize_negative_feedback(result.get("negative_sentences", []))
        result['precomputed_negative_summary'] = neg_summary 
        print(f"   [{festival_name}] 부정 문장 요약 완료.")
        
        festival_full_results.append(result)

        # 집계
        agg_pos += result.get("total_pos", 0)
        agg_neg += result.get("total_neg", 0)
        agg_strong_pos += result.get("total_strong_pos", 0)
        agg_strong_neg += result.get("total_strong_neg", 0)
        agg_negative_sentences.extend(result.get("negative_sentences", []))
        for season, data in result.get("seasonal_data", {}).items():
             if season in agg_seasonal:
                agg_seasonal[season]["pos"] += data.get("pos", 0)
                agg_seasonal[season]["neg"] += data.get("neg", 0)
        
        # CSV용 데이터 생성
        total_freq = result.get("total_sentiment_frequency", 0)
        pos_perc = (result.get('total_pos', 0) / total_freq * 100) if total_freq > 0 else 0.0
        neg_perc = (result.get('total_neg', 0) / total_freq * 100) if total_freq > 0 else 0.0
        
        category_results.append({
            "축제명": festival_name,
            '감성 빈도': result.get('total_sentiment_frequency', 0),
            '감성 점수': f"{result.get('total_sentiment_score', 50.0):.1f}",
            "긍정 문장 수": result.get("total_pos", 0),
            "부정 문장 수": result.get("total_neg", 0),
            "긍정 비율 (%)": f"{pos_perc:.1f}",
            "부정 비율 (%)": f"{neg_perc:.1f}", 
            '주요 불만 사항 요약': neg_summary if neg_summary else "없음"
        })

        if "blog_results_df" in result and not result["blog_results_df"].empty:
            all_blog_posts_list.append(result["blog_results_df"])

    if not category_results: 
        return {"error": f"선택된 카테고리 '{category_name}' 내 모든 축제({total_festivals}개)에서 유효한 분석 결과를 얻지 못했습니다."}

    total_sentiment_frequency = agg_pos + agg_neg
    total_sentiment_score = ((agg_strong_pos - agg_strong_neg) / total_sentiment_frequency * 50 + 50) if total_sentiment_frequency > 0 else 50.0

    all_blog_judgments = []
    for res in festival_full_results:
        all_blog_judgments.extend(res.get("blog_judgments", []))

    final_category_df = pd.DataFrame(category_results) if category_results else pd.DataFrame()
    final_all_blogs_df = pd.concat(all_blog_posts_list, ignore_index=True) if all_blog_posts_list else pd.DataFrame()

    return {
        "status": f"총 {total_festivals}개 축제 요청 중 {len(category_results)}개 분석 완료.",
        "total_pos": agg_pos, "total_neg": agg_neg, 
        "total_sentiment_frequency": total_sentiment_frequency,
        "total_sentiment_score": total_sentiment_score,
        "seasonal_data": agg_seasonal,
        "negative_sentences": agg_negative_sentences, # 카테고리 전체 요약용
        "individual_festival_results_df": final_category_df,
        "all_blog_posts_df": final_all_blogs_df,
        "festival_full_results": festival_full_results, 
        "all_blog_judgments": all_blog_judgments
    }