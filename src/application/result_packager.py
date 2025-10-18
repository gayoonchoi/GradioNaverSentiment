# src/application/result_packager.py
import gradio as gr
import pandas as pd
from .utils import save_df_to_csv, change_page, summarize_negative_feedback
from ..infrastructure.reporting.charts import create_donut_chart, create_stacked_bar_chart
import traceback

def package_keyword_results(results: dict, name: str):
    num_outputs = 20
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * (num_outputs - 1)

    try:
        neg_summary_text = results.get("precomputed_negative_summary")
        if neg_summary_text is None:
             neg_summary_text = summarize_negative_feedback(results.get("negative_sentences", []))

        overall_summary_text = f"""
- **긍정 문장 수**: {results.get('total_pos', 0)}개
- **부정 문장 수**: {results.get('total_neg', 0)}개
- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개
- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)"""

        # --- CSV 생성 ---
        summary_df_data = {
            '검색어': name, '감성 빈도': results.get('total_sentiment_frequency', 0),
            '감성 점수': f"{results.get('total_sentiment_score', 50.0):.1f}",
            '긍정 문장 수': results.get("total_pos", 0), '부정 문장 수': results.get("total_neg", 0),
        }
        total_freq = results.get('total_sentiment_frequency', 0)
        summary_df_data['긍정 비율 (%)'] = f"{(results.get('total_pos', 0) / total_freq * 100):.1f}" if total_freq > 0 else "0.0"
        summary_df_data['부정 비율 (%)'] = f"{(results.get('total_neg', 0) / total_freq * 100):.1f}" if total_freq > 0 else "0.0"
        summary_df_data['주요 불만 사항 요약'] = neg_summary_text if neg_summary_text else "없음"
        summary_df = pd.DataFrame([summary_df_data])
        summary_csv = save_df_to_csv(summary_df, "overall_summary", name)

        blog_df = results.get("blog_results_df", pd.DataFrame()) # 원본 DF (요약 포함)
        blog_list_csv = None
        if not blog_df.empty:
            blog_df_for_csv = blog_df.copy()
            if '긍/부정 문장 요약' in blog_df_for_csv.columns:
                 blog_df_for_csv['긍/부정 문장 요약'] = blog_df_for_csv['긍/부정 문장 요약'].astype(str).str.slice(0, 50) + '...'
            blog_list_csv = save_df_to_csv(blog_df_for_csv, "blog_list", name)

        # --- UI 표시용 데이터 준비 ---
        df_for_state = blog_df # State에는 원본 DF 전달
        initial_page_df, current_page, total_pages_str = change_page(df_for_state, 1) # 페이지네이션 및 표시는 원본 DF 기준

        seasonal_data = results.get("seasonal_data", {})
        spring_pos = seasonal_data.get("봄", {}).get("pos", 0); spring_neg = seasonal_data.get("봄", {}).get("neg", 0)
        summer_pos = seasonal_data.get("여름", {}).get("pos", 0); summer_neg = seasonal_data.get("여름", {}).get("neg", 0)
        autumn_pos = seasonal_data.get("가을", {}).get("pos", 0); autumn_neg = seasonal_data.get("가을", {}).get("neg", 0)
        winter_pos = seasonal_data.get("겨울", {}).get("pos", 0); winter_neg = seasonal_data.get("겨울", {}).get("neg", 0)

        return (
            results.get("status", "분석 완료"), results.get("url_markdown", "분석된 URL 없음"),
            gr.update(value=neg_summary_text, visible=bool(neg_summary_text)),
            gr.update(value=create_donut_chart(results.get("total_pos", 0), results.get("total_neg", 0), f'{name} 전체 후기 요약'), visible=results.get("total_pos", 0) > 0 or results.get("total_neg", 0) > 0),
            gr.update(value=overall_summary_text, visible=True),
            gr.update(value=summary_csv, visible=summary_csv is not None),
            gr.update(value=create_stacked_bar_chart(spring_pos, spring_neg, "봄 시즌"), visible=spring_pos > 0 or spring_neg > 0),
            gr.update(value=create_stacked_bar_chart(summer_pos, summer_neg, "여름 시즌"), visible=summer_pos > 0 or summer_neg > 0),
            gr.update(value=create_stacked_bar_chart(autumn_pos, autumn_neg, "가을 시즌"), visible=autumn_pos > 0 or autumn_neg > 0),
            gr.update(value=create_stacked_bar_chart(winter_pos, winter_neg, "겨울 시즌"), visible=winter_pos > 0 or winter_neg > 0),
            initial_page_df, # UI 표에는 첫 페이지만
            df_for_state, # State에는 전체 원본 DF
            results.get("blog_judgments", []), # State
            current_page,
            total_pages_str,
            gr.update(value=blog_list_csv, visible=blog_list_csv is not None),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)
        )
    except Exception as e:
        print(f"결과 패키징 중 오류 ({name}): {e}")
        traceback.print_exc()
        error_message = f"'{name}' 분석 결과 처리 중 오류 발생: {e}"
        return [error_message] + [gr.update(visible=False)] * (num_outputs - 1)


def package_festival_details(results: dict, name: str):
    # (이전과 동일 - 변경 없음)
    num_outputs = 8
    if "error" in results:
        return [gr.update(value=results["error"], visible=True)] + [gr.update(visible=False)] * (num_outputs - 1)
    try:
        neg_summary_text = results.get("precomputed_negative_summary", "")
        overall_summary_text = f"""
- **긍정 문장 수**: {results.get('total_pos', 0)}개
- **부정 문장 수**: {results.get('total_neg', 0)}개
- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개
- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)"""
        seasonal_data = results.get("seasonal_data", {})
        spring_pos = seasonal_data.get("봄", {}).get("pos", 0); spring_neg = seasonal_data.get("봄", {}).get("neg", 0)
        summer_pos = seasonal_data.get("여름", {}).get("pos", 0); summer_neg = seasonal_data.get("여름", {}).get("neg", 0)
        autumn_pos = seasonal_data.get("가을", {}).get("pos", 0); autumn_neg = seasonal_data.get("가을", {}).get("neg", 0)
        winter_pos = seasonal_data.get("겨울", {}).get("pos", 0); winter_neg = seasonal_data.get("겨울", {}).get("neg", 0)
        return [
            gr.update(value=neg_summary_text, visible=bool(neg_summary_text)),
            gr.update(value=create_donut_chart(results.get("total_pos", 0), results.get("total_neg", 0), f'{name} 후기 요약'), visible=results.get("total_pos", 0) > 0 or results.get("total_neg", 0) > 0),
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
         error_message = f"'{name}' 상세 정보 처리 중 오류 발생: {e}"
         return [error_message] + [gr.update(visible=False)] * (num_outputs - 1)


def package_category_results(results: dict, name: str):
    num_outputs = 33 # UI 컴포넌트 개수 재확인
    if "error" in results: return [results["error"]] + [gr.update(visible=False)] * (num_outputs - 1)

    try:
        cat_neg_summary_text = summarize_negative_feedback(results.get("negative_sentences", []))
        cat_overall_summary_text = f"""
- **긍정 문장 수**: {results.get('total_pos', 0)}개
- **부정 문장 수**: {results.get('total_neg', 0)}개
- **감성어 빈도 (긍정+부정)**: {results.get('total_sentiment_frequency', 0)}개
- **감성 점수**: {results.get('total_sentiment_score', 50.0):.1f}점 (0~100점)"""

        # --- CSV 생성 ---
        # ... (CSV 생성 로직 동일) ...
        summary_df_data = {
            '카테고리': name, '감성 빈도': results.get('total_sentiment_frequency', 0),
            '감성 점수': f"{results.get('total_sentiment_score', 50.0):.1f}",
            '긍정 문장 수': results.get("total_pos", 0), '부정 문장 수': results.get("total_neg", 0),
        }
        total_freq_cat = results.get('total_sentiment_frequency', 0)
        summary_df_data['긍정 비율 (%)'] = f"{(results.get('total_pos', 0) / total_freq_cat * 100):.1f}" if total_freq_cat > 0 else "0.0"
        summary_df_data['부정 비율 (%)'] = f"{(results.get('total_neg', 0) / total_freq_cat * 100):.1f}" if total_freq_cat > 0 else "0.0"
        summary_df_data['주요 불만 사항 요약'] = cat_neg_summary_text if cat_neg_summary_text else "없음"
        cat_summary_df = pd.DataFrame([summary_df_data])
        cat_overall_csv = save_df_to_csv(cat_summary_df, "category_summary", name)

        festival_df = results.get("individual_festival_results_df", pd.DataFrame())
        festival_list_csv = save_df_to_csv(festival_df, "festival_summary", name)

        all_blogs_df = results.get("all_blog_posts_df", pd.DataFrame()) # 원본 DF (요약 포함)
        all_blogs_list_csv = None
        if not all_blogs_df.empty:
            blog_df_for_csv = all_blogs_df.copy()
            if '긍/부정 문장 요약' in blog_df_for_csv.columns:
                 blog_df_for_csv['긍/부정 문장 요약'] = blog_df_for_csv['긍/부정 문장 요약'].astype(str).str.slice(0, 50) + '...'
            all_blogs_list_csv = save_df_to_csv(blog_df_for_csv, "all_blogs", name)

        # --- UI 표시용 데이터 준비 ---
        festival_page_df, festival_page_num, festival_pages_str = change_page(festival_df, 1) # 축제 표
        
        blogs_df_for_state = all_blogs_df # State에는 원본 블로그 DF
        blog_page_df, blog_page_num, blog_pages_str = change_page(blogs_df_for_state, 1) # 블로그 표

        agg_seasonal = results.get("seasonal_data", {})
        cat_spring_pos = agg_seasonal.get("봄", {}).get("pos", 0); cat_spring_neg = agg_seasonal.get("봄", {}).get("neg", 0)
        cat_summer_pos = agg_seasonal.get("여름", {}).get("pos", 0); cat_summer_neg = agg_seasonal.get("여름", {}).get("neg", 0)
        cat_autumn_pos = agg_seasonal.get("가을", {}).get("pos", 0); cat_autumn_neg = agg_seasonal.get("가을", {}).get("neg", 0)
        cat_winter_pos = agg_seasonal.get("겨울", {}).get("pos", 0); cat_winter_neg = agg_seasonal.get("겨울", {}).get("neg", 0)

        # 33개 컴포넌트에 대한 업데이트 반환
        return (
            # Tier 1 (9개)
            results.get("status", "분석 완료"),
            gr.update(value=cat_neg_summary_text, visible=bool(cat_neg_summary_text)),
            gr.update(value=create_donut_chart(results.get("total_pos", 0), results.get("total_neg", 0), f'{name} 종합 분석'), visible=results.get("total_pos", 0) > 0 or results.get("total_neg", 0) > 0),
            gr.update(value=cat_overall_summary_text, visible=True),
            gr.update(value=cat_overall_csv, visible=cat_overall_csv is not None),
            gr.update(value=create_stacked_bar_chart(cat_spring_pos, cat_spring_neg, "봄 시즌"), visible=cat_spring_pos > 0 or cat_spring_neg > 0),
            gr.update(value=create_stacked_bar_chart(cat_summer_pos, cat_summer_neg, "여름 시즌"), visible=cat_summer_pos > 0 or cat_summer_neg > 0),
            gr.update(value=create_stacked_bar_chart(cat_autumn_pos, cat_autumn_neg, "가을 시즌"), visible=cat_autumn_pos > 0 or cat_autumn_neg > 0),
            gr.update(value=create_stacked_bar_chart(cat_winter_pos, cat_winter_neg, "겨울 시즌"), visible=cat_winter_pos > 0 or cat_winter_neg > 0),
            # Tier 2 (14개)
            festival_page_df, festival_df, results.get("festival_full_results", []), festival_page_num, festival_pages_str,
            gr.update(value=festival_list_csv, visible=festival_list_csv is not None),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False),
            # Tier 3 (10개)
            blog_page_df,
            blogs_df_for_state, # State에는 원본 블로그 DF
            results.get("all_blog_judgments", []),
            blog_page_num,
            blog_pages_str,
            gr.update(value=all_blogs_list_csv, visible=all_blogs_list_csv is not None),
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False, open=False)
        )
    except Exception as e:
        print(f"카테고리 결과 패키징 중 오류 ({name}): {e}")
        traceback.print_exc()
        error_message = f"'{name}' 카테고리 결과 처리 중 오류 발생: {e}"
        return [error_message] + [gr.update(visible=False)] * (num_outputs - 1)