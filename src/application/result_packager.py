# src/application/result_packager.py
import gradio as gr
import pandas as pd
import os
from .utils import save_df_to_csv, change_page, summarize_negative_feedback
from ..infrastructure.reporting.charts import create_donut_chart, create_stacked_bar_chart
from ..infrastructure.reporting.wordclouds import create_wordcloud
import traceback

SEASON_EN_MAP = {
    "봄": "spring",
    "여름": "summer",
    "가을": "fall",
    "겨울": "winter"
}

def package_keyword_results(results: dict, name: str):
    num_outputs = 26
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * (num_outputs - 1)

    try:
        seasonal_texts = results.get("seasonal_texts", {})
        seasonal_wc_paths = {}
        for season, text in seasonal_texts.items():
            season_en = SEASON_EN_MAP.get(season)
            if text and season_en:
                mask_path = os.path.abspath(os.path.join("assets", f"mask_{season_en}.png"))
                seasonal_wc_paths[season] = create_wordcloud(text, f"{name}_{season}", mask_path=mask_path)
            else:
                seasonal_wc_paths[season] = None

        neg_summary_text = summarize_negative_feedback(results.get("negative_sentences", []))
        overall_summary_text = f"""- **긍정 문장 수**: {results.get('total_pos', 0)}개\n- **부정 문장 수**: {results.get('total_neg', 0)}개\n- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개\n- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)"""

        summary_df = pd.DataFrame([{
            '검색어': name, '감성 빈도': results.get('total_sentiment_frequency', 0),
            '감성 점수': f"{results.get('total_sentiment_score', 50.0):.1f}",
            '긍정 문장 수': results.get("total_pos", 0), '부정 문장 수': results.get("total_neg", 0)
        }])
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
            gr.update(value=summary_csv, visible=summary_csv is not None),
            gr.update(value=create_stacked_bar_chart(spring_pos, spring_neg, "봄 시즌"), visible=spring_pos > 0 or spring_neg > 0),
            gr.update(value=create_stacked_bar_chart(summer_pos, summer_neg, "여름 시즌"), visible=summer_pos > 0 or summer_neg > 0),
            gr.update(value=create_stacked_bar_chart(autumn_pos, autumn_neg, "가을 시즌"), visible=autumn_pos > 0 or autumn_neg > 0),
            gr.update(value=create_stacked_bar_chart(winter_pos, winter_neg, "겨울 시즌"), visible=winter_pos > 0 or winter_neg > 0),
            gr.update(value=seasonal_wc_paths.get("봄"), visible=seasonal_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_wc_paths.get("여름"), visible=seasonal_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_wc_paths.get("가을"), visible=seasonal_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_wc_paths.get("겨울"), visible=seasonal_wc_paths.get("겨울") is not None),
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
    num_outputs = 40
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * (num_outputs - 1)

    try:
        seasonal_texts = results.get("seasonal_texts", {})
        seasonal_wc_paths = {}
        for season, text in seasonal_texts.items():
            season_en = SEASON_EN_MAP.get(season)
            if text and season_en:
                mask_path = os.path.abspath(os.path.join("assets", f"mask_{season_en}.png"))
                seasonal_wc_paths[season] = create_wordcloud(text, f"{name}_{season}", mask_path=mask_path)
            else:
                seasonal_wc_paths[season] = None

        cat_neg_summary_text = summarize_negative_feedback(results.get("negative_sentences", []))
        cat_overall_summary_text = f"""- **긍정 문장 수**: {results.get('total_pos', 0)}개\n- **부정 문장 수**: {results.get('total_neg', 0)}개\n- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개\n- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)"""

        summary_df = pd.DataFrame([{
            '카테고리': name, '감성 빈도': results.get('total_sentiment_frequency', 0),
            '감성 점수': f"{results.get('total_sentiment_score', 50.0):.1f}",
            '긍정 문장 수': results.get("total_pos", 0), '부정 문장 수': results.get("total_neg", 0)
        }])
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
            gr.update(value=seasonal_wc_paths.get("봄"), visible=seasonal_wc_paths.get("봄") is not None),
            gr.update(value=seasonal_wc_paths.get("여름"), visible=seasonal_wc_paths.get("여름") is not None),
            gr.update(value=seasonal_wc_paths.get("가을"), visible=seasonal_wc_paths.get("가을") is not None),
            gr.update(value=seasonal_wc_paths.get("겨울"), visible=seasonal_wc_paths.get("겨울") is not None),
            festival_page_df, festival_df, results.get("festival_full_results", []), festival_page_num, festival_pages_str,
            gr.update(value=festival_list_csv, visible=festival_list_csv is not None),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False),
            blog_page_df, all_blogs_df, results.get("all_blog_judgments", []), blog_page_num, blog_pages_str, gr.update(visible=False),
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