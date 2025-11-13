# src/application/result_packager.py
import gradio as gr
import pandas as pd
import os
from .utils import save_df_to_csv, change_page, summarize_negative_feedback
from ..infrastructure.reporting.charts import create_donut_chart, create_stacked_bar_chart
# create_wordcloud 대신 create_sentiment_wordclouds를 임포트
from ..infrastructure.reporting.wordclouds import create_sentiment_wordclouds
import traceback

SEASON_EN_MAP = {
    "봄": "spring",
    "여름": "summer",
    "가을": "fall",
    "겨울": "winter"
}

def package_keyword_results(results: dict, name: str):
    # 출력 개수가 5개(계절별 부정 WC + 트렌드 요약) 늘어났으므로 30으로 수정
    num_outputs = 30
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * (num_outputs - 1)

    try:
        # seasonal_texts 대신 seasonal_aspect_pairs를 사용
        seasonal_aspect_pairs = results.get("seasonal_aspect_pairs", {})
        seasonal_pos_wc_paths = {}
        seasonal_neg_wc_paths = {}
        
        # seasonal_aspect_pairs를 순회
        for season, pairs in seasonal_aspect_pairs.items():
            season_en = SEASON_EN_MAP.get(season)
            # 텍스트 유무가 아닌, 쌍(pair) 데이터 유무를 확인
            if pairs and season_en:
                mask_path = os.path.abspath(os.path.join("assets", f"mask_{season_en}.png"))
                # text 대신 pairs를 전달
                pos_path, neg_path = create_sentiment_wordclouds(pairs, f"{name}_{season}", mask_path=mask_path)
                seasonal_pos_wc_paths[season] = pos_path
                seasonal_neg_wc_paths[season] = neg_path
            else:
                seasonal_pos_wc_paths[season] = None
                seasonal_neg_wc_paths[season] = None

        neg_summary_text = summarize_negative_feedback(results.get("negative_sentences", []))
        
        trend_metrics = results.get("trend_metrics", {})
        trend_summary_text = f"""- **축제 전 30일 평균 검색량**: {trend_metrics.get('before_avg', 'N/A')}
- **축제 기간 평균 검색량**: {trend_metrics.get('during_avg', 'N/A')}
- **축제 후 30일 평균 검색량**: {trend_metrics.get('after_avg', 'N/A')}
- **트렌드 지수 (축제 전 대비 기간)**: {trend_metrics.get('trend_index', 'N/A')}%
- **축제 후 트렌드 (기간 대비)**: {trend_metrics.get('after_trend_index', 'N/A')}%
"""

        overall_summary_text = f"""- **긍정 문장 수**: {results.get('total_pos', 0)}개
- **부정 문장 수**: {results.get('total_neg', 0)}개
- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개
- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)
- **만족도 변화 (감성점수 - 트렌드지수)**: {results.get('satisfaction_delta', 0):.1f}
"""

        summary_df_data = {
            '검색어': name,
            '감성 빈도': results.get('total_sentiment_frequency', 0),
            '감성 점수': f"{results.get('total_sentiment_score', 50.0):.1f}",
            '긍정 문장 수': results.get("total_pos", 0),
            '부정 문장 수': results.get("total_neg", 0),
            '축제 기간 (일)': results.get('event_period', 'N/A'),
            '트렌드 지수 (%)': trend_metrics.get('trend_index', 'N/A'),
            '만족도 변화': f"{results.get('satisfaction_delta', 0):.1f}",
            '주요 감성 키워드': str(results.get('emotion_keyword_freq', {}))
        }
        summary_df = pd.DataFrame([summary_df_data])
        
        summary_csv = save_df_to_csv(summary_df, "overall_summary", name)
        blog_df = results.get("blog_results_df", pd.DataFrame())
        blog_list_csv = save_df_to_csv(blog_df, "blog_list", name)
        df_for_state = blog_df
        initial_page_df, current_page, total_pages_str = change_page(df_for_state, 1)

        seasonal_data = results.get("seasonal_data", {})
        spring_pos = seasonal_data.get("봄", {}).get("pos", 0); spring_neg = seasonal_data.get("봄", {}).get("neg", 0)
        summer_pos = seasonal_data.get("여름", {}).get("pos", 0); summer_neg = seasonal_data.get("여름", {}).get("neg", 0)
        autumn_pos = seasonal_data.get("가을", {}).get("pos", 0); autumn_neg = seasonal_data.get("가을", {}).get("neg", 0)
        winter_pos = seasonal_data.get("겨울", {}).get("pos", 0); winter_neg = seasonal_data.get("겨울", {}).get("neg", 0)
        trend_graph = results.get("trend_graph")

        return (
            results.get("status", "분석 완료"),
            results.get("url_markdown", "분석된 URL 없음"),
            gr.update(value=neg_summary_text, visible=bool(neg_summary_text)),
            gr.update(value=create_donut_chart(results.get("total_pos", 0), results.get("total_neg", 0), f'{name} 전체 후기 요약'), visible=True),
            gr.update(value=trend_graph, visible=trend_graph is not None),
            gr.update(value=overall_summary_text, visible=True),
            gr.update(value=trend_summary_text, visible=bool(trend_metrics)),
            gr.update(value=summary_csv, visible=summary_csv is not None),
            gr.update(value=create_stacked_bar_chart(spring_pos, spring_neg, "봄 시즌"), visible=spring_pos > 0 or spring_neg > 0),
            gr.update(value=create_stacked_bar_chart(summer_pos, summer_neg, "여름 시즌"), visible=summer_pos > 0 or summer_neg > 0),
            gr.update(value=create_stacked_bar_chart(autumn_pos, autumn_neg, "가을 시즌"), visible=autumn_pos > 0 or autumn_neg > 0),
            gr.update(value=create_stacked_bar_chart(winter_pos, winter_neg, "겨울 시즌"), visible=winter_pos > 0 or winter_neg > 0),
            
            gr.update(value=seasonal_pos_wc_paths.get("봄"), visible=seasonal_pos_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("봄"), visible=seasonal_neg_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_pos_wc_paths.get("여름"), visible=seasonal_pos_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("여름"), visible=seasonal_neg_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_pos_wc_paths.get("가을"), visible=seasonal_pos_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("가을"), visible=seasonal_neg_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_pos_wc_paths.get("겨울"), visible=seasonal_pos_wc_paths.get("겨울") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("겨울"), visible=seasonal_neg_wc_paths.get("겨울") is not None),
            
            initial_page_df, df_for_state, results.get("blog_judgments", []),
            current_page, total_pages_str,
            gr.update(value=blog_list_csv, visible=blog_list_csv is not None),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)
        )
    except Exception as e:
        print(f"결과 패키징 중 오류 ({name}): {e}")
        traceback.print_exc()
        return [f"오류: {e}"] + [gr.update(visible=False)] * (num_outputs - 1)

def package_category_results(results: dict, name: str):
    num_outputs = 48 # 4개의 트렌드 워드클라우드 추가
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * (num_outputs - 1)

    try:
        seasonal_aspect_pairs = results.get("seasonal_aspect_pairs", {})
        seasonal_pos_wc_paths = {}
        seasonal_neg_wc_paths = {}
        for season, pairs in seasonal_aspect_pairs.items():
            season_en = SEASON_EN_MAP.get(season)
            if pairs and season_en:
                mask_path = os.path.abspath(os.path.join("assets", f"mask_{season_en}.png"))
                pos_path, neg_path = create_sentiment_wordclouds(pairs, f"{name}_{season}", mask_path=mask_path)
                seasonal_pos_wc_paths[season] = pos_path
                seasonal_neg_wc_paths[season] = neg_path
            else:
                seasonal_pos_wc_paths[season] = None
                seasonal_neg_wc_paths[season] = None
        
        seasonal_trend_wc_paths = results.get("seasonal_trend_wc_paths", {})

        cat_neg_summary_text = summarize_negative_feedback(results.get("negative_sentences", []))
        cat_overall_summary_text = f"""- **긍정 문장 수**: {results.get('total_pos', 0)}개
- **부정 문장 수**: {results.get('total_neg', 0)}개
- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개
- **종합 감성 점수 (가중 평균)**: {results.get('total_sentiment_score', 50.0):.1f}점
- **테마 평균 감성 점수 (단순 평균)**: {results.get('theme_sentiment_avg', 50.0):.1f}점
"""

        summary_df_data = {
            '카테고리': name, 
            '감성 빈도': results.get('total_sentiment_frequency', 0), 
            '종합 감성 점수': f"{results.get('total_sentiment_score', 50.0):.1f}",
            '테마 평균 감성 점수': f"{results.get('theme_sentiment_avg', 50.0):.1f}",
            '긍정 문장 수': results.get("total_pos", 0), 
            '부정 문장 수': results.get("total_neg", 0)
        }
        summary_df = pd.DataFrame([summary_df_data])
        cat_overall_csv = save_df_to_csv(summary_df, "category_summary", name)

        festival_df = results.get("individual_festival_results_df", pd.DataFrame())
        festival_list_csv = save_df_to_csv(festival_df, "festival_summary", name)

        all_blogs_df = results.get("all_blog_posts_df", pd.DataFrame())
        all_blogs_list_csv = save_df_to_csv(all_blogs_df, "all_blogs", name)

        festival_page_df, festival_page_num, festival_pages_str = change_page(festival_df, 1)
        blog_page_df, blog_page_num, blog_pages_str = change_page(all_blogs_df, 1)

        seasonal_data = results.get("seasonal_data", {})
        cat_spring_pos = seasonal_data.get("봄", {}).get("pos", 0); cat_spring_neg = seasonal_data.get("봄", {}).get("neg", 0)
        cat_summer_pos = seasonal_data.get("여름", {}).get("pos", 0); cat_summer_neg = seasonal_data.get("여름", {}).get("neg", 0)
        cat_autumn_pos = seasonal_data.get("가을", {}).get("pos", 0); cat_autumn_neg = seasonal_data.get("가을", {}).get("neg", 0)
        cat_winter_pos = seasonal_data.get("겨울", {}).get("pos", 0); cat_winter_neg = seasonal_data.get("겨울", {}).get("neg", 0)

        return (
            results.get("status", "분석 완료"),
            gr.update(value=cat_neg_summary_text, visible=bool(cat_neg_summary_text)),
            gr.update(value=create_donut_chart(results.get("total_pos", 0), results.get("total_neg", 0), f'{name} 종합 분석'), visible=True),
            gr.update(value=cat_overall_summary_text, visible=True),
            gr.update(value=cat_overall_csv, visible=cat_overall_csv is not None),
            gr.update(value=create_stacked_bar_chart(cat_spring_pos, cat_spring_neg, "봄 시즌"), visible=cat_spring_pos > 0 or cat_spring_neg > 0),
            gr.update(value=create_stacked_bar_chart(cat_summer_pos, cat_summer_neg, "여름 시즌"), visible=cat_summer_pos > 0 or cat_summer_neg > 0),
            gr.update(value=create_stacked_bar_chart(cat_autumn_pos, cat_autumn_neg, "가을 시즌"), visible=cat_autumn_pos > 0 or cat_autumn_neg > 0),
            gr.update(value=create_stacked_bar_chart(cat_winter_pos, cat_winter_neg, "겨울 시즌"), visible=cat_winter_pos > 0 or cat_winter_neg > 0),
            
            gr.update(value=seasonal_pos_wc_paths.get("봄"), visible=seasonal_pos_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("봄"), visible=seasonal_neg_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_pos_wc_paths.get("여름"), visible=seasonal_pos_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("여름"), visible=seasonal_neg_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_pos_wc_paths.get("가을"), visible=seasonal_pos_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("가을"), visible=seasonal_neg_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_pos_wc_paths.get("겨울"), visible=seasonal_pos_wc_paths.get("겨울") is not None),
            gr.update(value=seasonal_neg_wc_paths.get("겨울"), visible=seasonal_neg_wc_paths.get("겨울") is not None),

            gr.update(value=seasonal_trend_wc_paths.get("봄"), visible=seasonal_trend_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_trend_wc_paths.get("여름"), visible=seasonal_trend_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_trend_wc_paths.get("가을"), visible=seasonal_trend_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_trend_wc_paths.get("겨울"), visible=seasonal_trend_wc_paths.get("겨울") is not None),

            festival_page_df, festival_df, results.get("festival_full_results", []), festival_page_num, festival_pages_str,
            gr.update(value=festival_list_csv, visible=festival_list_csv is not None),
            
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 
            gr.update(visible=False, open=False),
            
            blog_page_df, all_blogs_df, results.get("all_blog_judgments", []), blog_page_num, blog_pages_str, 
            gr.update(value=all_blogs_list_csv, visible=all_blogs_list_csv is not None),
            
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)
        )

    except Exception as e:
        print(f"카테고리 결과 패키징 중 오류 ({name}): {e}")
        traceback.print_exc()
        return [f"오류: {e}"] + [gr.update(visible=False)] * (num_outputs - 1)

def package_festival_details(results: dict, name: str):
    num_outputs = 8
    if "error" in results: return [gr.update(value=results["error"], visible=True)] + [gr.update(visible=False)] * (num_outputs - 1)
    try:
        neg_summary_text = results.get("precomputed_negative_summary", "")
        overall_summary_text = f"""- **긍정 문장 수**: {results.get('total_pos', 0)}개\n- **부정 문장 수**: {results.get('total_neg', 0)}개\n- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개\n- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)"""
        seasonal_data = results.get("seasonal_data", {})
        spring_pos = seasonal_data.get("봄", {}).get("pos", 0); spring_neg = seasonal_data.get("봄", {}).get("neg", 0)
        summer_pos = seasonal_data.get("여름", {}).get("pos", 0); summer_neg = seasonal_data.get("여름", {}).get("neg", 0)
        autumn_pos = seasonal_data.get("가을", {}).get("pos", 0); autumn_neg = seasonal_data.get("가을", {}).get("neg", 0)
        winter_pos = seasonal_data.get("겨울", {}).get("pos", 0); winter_neg = seasonal_data.get("겨울", {}).get("neg", 0)
        
        return [
            gr.update(value=neg_summary_text, visible=bool(neg_summary_text)),
            gr.update(value=create_donut_chart(results.get("total_pos", 0), results.get("total_neg", 0), f'{name} 후기 요약'), visible=True),
            gr.update(value=overall_summary_text, visible=True),
            gr.update(value=create_stacked_bar_chart(spring_pos, spring_neg, "봄 시즌"), visible=spring_pos > 0 or spring_neg > 0),
            gr.update(value=create_stacked_bar_chart(summer_pos, summer_neg, "여름 시즌"), visible=summer_pos > 0 or summer_neg > 0),
            gr.update(value=create_stacked_bar_chart(autumn_pos, autumn_neg, "가을 시즌"), visible=autumn_pos > 0 or autumn_neg > 0),
            gr.update(value=create_stacked_bar_chart(winter_pos, winter_neg, "겨울 시즌"), visible=winter_pos > 0 or winter_neg > 0),
            gr.update(visible=True, open=True)
        ]
    except Exception as e:
         print(f"축제 상세 정보 패키징 중 오류 ({name}): {e}")
         traceback.print_exc()
         return [f"오류: {e}"] + [gr.update(visible=False)] * (num_outputs - 1)