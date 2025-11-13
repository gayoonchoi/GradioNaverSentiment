# src/application/analysis_logic.py
import pandas as pd
import re
import traceback
import gradio as gr
import os
from datetime import datetime
from ..data import festival_loader
from .utils import get_season, summarize_negative_feedback, calculate_trend_metrics
from ..application.graph import app_llm_graph
from ..infrastructure.web.naver_api import search_naver_blog_page
from ..infrastructure.web.scraper import scrape_blog_content
from ..infrastructure.web.naver_trend_api import create_trend_graph
from ..infrastructure.web.tour_api_client import get_festival_period
from collections import Counter

def analyze_single_keyword_fully(keyword: str, num_reviews: int, driver, log_details: bool, progress: gr.Progress, progress_desc: str):
    # TourAPI에서 축제 기간 가져오기
    start_date_str, end_date_str = get_festival_period(keyword)
    event_period = None
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, "%Y%m%d")
            end_date = datetime.strptime(end_date_str, "%Y%m%d")
            event_period = (end_date - start_date).days + 1
        except ValueError:
            start_date, end_date = None, None
    else:
        start_date, end_date = None, None

    search_keyword = f"{keyword} 후기"
    max_candidates = max(50, num_reviews * 10)
    candidate_blogs, blog_results_list, all_negative_sentences = [], [], []
    blog_judgments_list = []
    emotion_keywords = []
    seasonal_aspect_pairs = {"봄": [], "여름": [], "가을": [], "겨울": [], "정보없음": []}
    seasonal_texts = {"봄": [], "여름": [], "가을": [], "겨울": [], "정보없음": []}
    total_pos, total_neg, total_searched, start_index = 0, 0, 0, 1
    total_strong_pos, total_strong_neg = 0, 0
    seasonal_data = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}, "정보없음": {"pos": 0, "neg": 0}}

    try:
        max_api_calls = 10
        for call_num in range(max_api_calls):
            if len(candidate_blogs) >= max_candidates: break
            progress((call_num + 1) / max_api_calls * 0.2, desc=f"[{progress_desc}] {keyword} 블로그 후보 수집 중... ({len(candidate_blogs)}/{max_candidates})")
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

    valid_blogs_data = []
    num_candidates_to_process = len(candidate_blogs)
    initial_progress = 0.2
    
    for i, blog_data in enumerate(candidate_blogs):
        if len(valid_blogs_data) >= num_reviews: break
        progress(initial_progress + (i + 1) / num_candidates_to_process * 0.8, desc=f"[{progress_desc}] {keyword} 분석 중... ({len(valid_blogs_data)}/{num_reviews} 완료, {i+1}/{num_candidates_to_process} 확인)")

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
            
            for j in judgments:
                if j.get("sentiment_keyword"):
                    emotion_keywords.append(j["sentiment_keyword"])

            season = get_season(blog_data.get('postdate', ''))
            seasonal_texts[season].append(content)
            
            aspect_pairs = final_state.get("aspect_sentiment_pairs", [])
            if aspect_pairs:
                seasonal_aspect_pairs[season].extend(aspect_pairs)

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
    
    trend_graph_path, trend_df = create_trend_graph(keyword, festival_start_date=start_date, festival_end_date=end_date)
    
    trend_metrics = calculate_trend_metrics(trend_df, start_date, end_date)
    satisfaction_delta = total_sentiment_score - trend_metrics.get("trend_index", 0)
    
    emotion_keyword_freq = Counter(emotion_keywords)

    return {
        "status": f"총 {total_searched}개 검색, {len(candidate_blogs)}개 후보 중 {len(valid_blogs_data)}개 블로그 최종 분석 완료.",
        "total_pos": total_pos, "total_neg": total_neg, "total_strong_pos": total_strong_pos, "total_strong_neg": total_strong_neg,
        "total_sentiment_frequency": total_sentiment_frequency, "total_sentiment_score": total_sentiment_score,
        "seasonal_data": seasonal_data, 
        "negative_sentences": all_negative_sentences, 
        "blog_results_df": pd.DataFrame(blog_results_list) if blog_results_list else pd.DataFrame(),
        "blog_judgments": blog_judgments_list,
        "url_markdown": f"### 분석된 블로그 URL ({len(valid_blogs_data)}개)\n" + "\n".join([f"- [{b['title']}]({b['link']})" for b in valid_blogs_data]),
        "trend_graph": trend_graph_path,
        "trend_df": trend_df,
        "event_period": event_period,
        "festival_start_date": start_date,
        "festival_end_date": end_date,
        "trend_metrics": trend_metrics,
        "satisfaction_delta": satisfaction_delta,
        "emotion_keyword_freq": dict(emotion_keyword_freq.most_common(20)), # 상위 20개만
        "seasonal_texts": {k: "\n".join(v) for k, v in seasonal_texts.items()},
        "seasonal_aspect_pairs": seasonal_aspect_pairs
    }

# 핵심 분석 로직을 담는 새 함수
from ..infrastructure.reporting.wordclouds import create_seasonal_trend_wordcloud
from ..application.result_packager import SEASON_EN_MAP

def perform_festival_group_analysis(festivals_to_analyze: list, group_name: str, num_reviews: int, driver, log_details: bool, progress: gr.Progress, initial_progress: float, total_steps: int):
    if not festivals_to_analyze: return {"error": f"'{group_name}' 그룹에서 분석할 축제를 찾을 수 없습니다."}

    category_results, all_blog_posts_list = [], []
    festival_full_results = []
    agg_pos, agg_neg = 0, 0
    agg_strong_pos, agg_strong_neg = 0, 0
    agg_seasonal = {"봄": {"pos": 0, "neg": 0}, "여름": {"pos": 0, "neg": 0}, "가을": {"pos": 0, "neg": 0}, "겨울": {"pos": 0, "neg": 0}, "정보없음": {"pos": 0, "neg": 0}}
    agg_negative_sentences = []
    agg_seasonal_texts = {"봄": [], "여름": [], "가을": [], "겨울": [], "정보없음": []}
    agg_seasonal_aspect_pairs = {"봄": [], "여름": [], "가을": [], "겨울": [], "정보없음": []}
    seasonal_trend_scores = {"봄": {}, "여름": {}, "가을": {}, "겨울": {}}
    total_festivals_sentiment_score = 0
    analyzed_festivals_count = 0

    total_festivals = len(festivals_to_analyze)
    for i, festival_name in enumerate(festivals_to_analyze):
        def nested_progress_callback(p, desc=""):
            progress(initial_progress + (i + p) / total_festivals / total_steps, desc=f"분석 중: {festival_name} ({i+1}/{total_festivals}) - {desc}")

        result = analyze_single_keyword_fully(festival_name, num_reviews, driver, log_details, nested_progress_callback, "그룹 분석")
        
        if "error" in result or result.get("blog_results_df", pd.DataFrame()).empty:
            print(f"   [{festival_name}] 분석 결과가 없거나 오류 발생.")
            continue

        result['precomputed_negative_summary'] = summarize_negative_feedback(result.get("negative_sentences", []))
        festival_full_results.append(result)

        # 시즌별 트렌드 점수 집계
        festival_start_date = result.get("festival_start_date")
        trend_df = result.get("trend_df")
        if festival_start_date and not trend_df.empty:
            season = get_season(festival_start_date.strftime("%Y%m%d"))
            if season != "정보없음":
                peak_trend_score = trend_df['ratio'].max()
                seasonal_trend_scores[season][festival_name] = peak_trend_score

        agg_pos += result.get("total_pos", 0)
        agg_neg += result.get("total_neg", 0)
        agg_strong_pos += result.get("total_strong_pos", 0)
        agg_strong_neg += result.get("total_strong_neg", 0)
        agg_negative_sentences.extend(result.get("negative_sentences", []))
        
        for season, pairs in result.get("seasonal_aspect_pairs", {}).items():
            if pairs:
                agg_seasonal_aspect_pairs[season].extend(pairs)

        for season, texts in result.get("seasonal_texts", {}).items():
            if texts: agg_seasonal_texts[season].append(texts)
        for season, data in result.get("seasonal_data", {}).items():
            agg_seasonal[season]["pos"] += data.get("pos", 0)
            agg_seasonal[season]["neg"] += data.get("neg", 0)
        
        total_freq = result.get("total_sentiment_frequency", 0)
        sentiment_score = result.get('total_sentiment_score', 50.0)
        pos_perc = (result.get('total_pos', 0) / total_freq * 100) if total_freq > 0 else 0.0
        neg_perc = (result.get('total_neg', 0) / total_freq * 100) if total_freq > 0 else 0.0
        
        total_festivals_sentiment_score += sentiment_score
        analyzed_festivals_count += 1
        
        trend_metrics = result.get("trend_metrics", {})
        
        category_results.append({
            "축제명": festival_name,
            '감성 빈도': total_freq,
            '감성 점수': f"{sentiment_score:.1f}",
            "긍정 문장 수": result.get("total_pos", 0),
            "부정 문장 수": result.get("total_neg", 0),
            "긍정 비율 (%)": f"{pos_perc:.1f}",
            "부정 비율 (%)": f"{neg_perc:.1f}",
            '축제 기간 (일)': result.get('event_period', 'N/A'),
            '트렌드 지수 (%)': trend_metrics.get('trend_index', 'N/A'),
            '만족도 변화': f"{result.get('satisfaction_delta', 0):.1f}",
            '주요 감성 키워드': str(result.get('emotion_keyword_freq', {})),
            '주요 불만 사항 요약': result['precomputed_negative_summary'] or "없음"
        })

        if "blog_results_df" in result and not result["blog_results_df"].empty:
            all_blog_posts_list.append(result["blog_results_df"])

    if not category_results: 
        return {"error": f"선택된 그룹 '{group_name}' 내 모든 축제({total_festivals}개)에서 유효한 분석 결과를 얻지 못했습니다."}

    # 계절별 트렌드 워드클라우드 생성
    seasonal_trend_wc_paths = {}
    for season, scores in seasonal_trend_scores.items():
        if scores:
            mask_path = os.path.abspath(os.path.join("assets", f"mask_{SEASON_EN_MAP.get(season)}.png"))
            wc_path = create_seasonal_trend_wordcloud(scores, f"{group_name}_{season}_트렌드", mask_path)
            seasonal_trend_wc_paths[season] = wc_path

    total_sentiment_frequency = agg_pos + agg_neg
    total_sentiment_score = ((agg_strong_pos - agg_strong_neg) / total_sentiment_frequency * 50 + 50) if total_sentiment_frequency > 0 else 50.0
    theme_sentiment_avg = total_festivals_sentiment_score / analyzed_festivals_count if analyzed_festivals_count > 0 else 0.0

    final_category_df = pd.DataFrame(category_results)
    final_all_blogs_df = pd.concat(all_blog_posts_list, ignore_index=True) if all_blog_posts_list else pd.DataFrame()

    return {
        "status": f"총 {total_festivals}개 축제 요청 중 {len(category_results)}개 분석 완료.",
        "total_pos": agg_pos, "total_neg": agg_neg, 
        "total_sentiment_frequency": total_sentiment_frequency,
        "total_sentiment_score": total_sentiment_score,
        "theme_sentiment_avg": theme_sentiment_avg,
        "seasonal_data": agg_seasonal,
        "negative_sentences": agg_negative_sentences,
        "seasonal_texts": {k: "\n".join(v) for k, v in agg_seasonal_texts.items()},
        "seasonal_aspect_pairs": agg_seasonal_aspect_pairs,
        "seasonal_trend_wc_paths": seasonal_trend_wc_paths, # 워드클라우드 경로 추가
        "individual_festival_results_df": final_category_df,
        "all_blog_posts_df": final_all_blogs_df,
        "festival_full_results": festival_full_results, 
        "all_blog_judgments": [j for res in festival_full_results for j in res.get("blog_judgments", [])]
    }

# 기존 함수는 새로 만든 그룹 분석 함수를 호출하는 래퍼(wrapper)가 됨
def perform_category_analysis(cat1, cat2, cat3, num_reviews, driver, log_details, progress: gr.Progress, initial_progress, total_steps):
    festivals_to_analyze = festival_loader.get_festivals(cat1, cat2, cat3)
    category_name = cat3 or cat2 or cat1
    return perform_festival_group_analysis(festivals_to_analyze, category_name, num_reviews, driver, log_details, progress, initial_progress, total_steps)