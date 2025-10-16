
import gradio as gr
import pandas as pd
from src.application.analysis_service import (
    analyze_keyword_and_generate_report, 
    run_comparison_analysis, 
    change_page,
    analyze_festivals_by_category,
    compare_categories
)
from src.data import festival_loader

def create_ui():
    # UI가 로드될 때 한 번만 대분류 목록을 가져옵니다.
    cat1_choices = festival_loader.get_cat1_choices()

    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("## 🚀 LLM 우선 네이버 블로그 감성 분석기")

        with gr.Tabs():
            with gr.TabItem("카테고리별 축제 분석"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("분석하고 싶은 축제의 카테고리를 선택하세요.")
                        cat1_dropdown = gr.Dropdown(label="대분류", choices=cat1_choices)
                        cat2_dropdown = gr.Dropdown(label="중분류", interactive=True)
                        cat3_dropdown = gr.Dropdown(label="소분류", interactive=True)
                        category_num_reviews = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="축제별 분석 리뷰 수")
                        category_analyze_button = gr.Button("카테고리 분석 시작", variant="primary")
                    with gr.Column(scale=2):
                        category_status_output = gr.Textbox(label="분석 상태", interactive=False)
                        gr.Markdown("### 카테고리 종합 분석 결과")
                        category_combined_chart = gr.Plot()
                        gr.Markdown("### 축제별 개별 분석 결과")
                        category_individual_charts = gr.Plot()

                # Dropdown 연동 로직
                def update_cat2_choices(cat1):
                    choices = festival_loader.get_cat2_choices(cat1)
                    return gr.update(choices=choices, value=None)

                def update_cat3_choices(cat1, cat2):
                    choices = festival_loader.get_cat3_choices(cat1, cat2)
                    return gr.update(choices=choices, value=None)

                cat1_dropdown.change(update_cat2_choices, inputs=cat1_dropdown, outputs=cat2_dropdown)
                cat2_dropdown.change(update_cat3_choices, inputs=[cat1_dropdown, cat2_dropdown], outputs=cat3_dropdown)

                # 분석 버튼 클릭 이벤트
                category_analyze_button.click(
                    analyze_festivals_by_category,
                    inputs=[cat1_dropdown, cat2_dropdown, cat3_dropdown, category_num_reviews],
                    outputs=[category_status_output, category_combined_chart, category_individual_charts]
                )

            with gr.TabItem("단일 키워드 분석"):
                # 기존 단일 키워드 분석 UI (수정됨)
                full_df_state = gr.State()
                with gr.Row():
                    with gr.Column(scale=1):
                        keyword_input = gr.Textbox(label="검색어", placeholder="예: 제주도 핫플")
                        num_reviews_input = gr.Slider(minimum=5, maximum=50, value=10, step=1, label="분석할 리뷰 수")
                        analyze_button = gr.Button("분석 시작", variant="primary")
                    with gr.Column(scale=2):
                        status_output = gr.Textbox(label="분석 상태", interactive=False)
                        url_output = gr.Markdown(label="수집된 전체 URL 리스트")
                        download_output = gr.File(label="분석 요약 보고서(CSV) 다운로드", visible=False)
                
                gr.Markdown("### 주요 불만 사항 요약")
                negative_summary_output = gr.Markdown(label="부정적 의견 요약", visible=False)
                negative_download_output = gr.File(label="부정적 의견 요약(CSV) 다운로드", visible=False)

                gr.Markdown("### 감성 분석 차트")
                with gr.Row():
                    overall_chart_output = gr.Plot(label="전체 후기 요약", visible=False)
                with gr.Row():
                    spring_chart_output = gr.Plot(label="봄 시즌", visible=False)
                    summer_chart_output = gr.Plot(label="여름 시즌", visible=False)
                    autumn_chart_output = gr.Plot(label="가을 시즌", visible=False)
                    winter_chart_output = gr.Plot(label="겨울 시즌", visible=False)

                gr.Markdown("### 개별 블로그 분석 결과")
                results_output = gr.DataFrame(headers=["블로그 제목", "링크", "긍정 문장 수", "부정 문장 수", "중립 문장 수", "긍정 비율 (%)", "긍/부정 문장 요약"], label="분석 결과", wrap=True)
                with gr.Row():
                    page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True)
                    total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False)
                
                page_num_input.submit(change_page, inputs=[full_df_state, page_num_input], outputs=[results_output, page_num_input, total_pages_output])

                analyze_button.click(
                    analyze_keyword_and_generate_report,
                    inputs=[keyword_input, num_reviews_input],
                    outputs=[
                        status_output,
                        overall_chart_output, 
                        spring_chart_output, 
                        summer_chart_output, 
                        autumn_chart_output, 
                        winter_chart_output,
                        download_output,
                        results_output,
                        url_output,
                        full_df_state,
                        page_num_input,
                        total_pages_output,
                        negative_summary_output,
                        negative_download_output
                    ]
                )

            with gr.TabItem("카테고리별 축제 비교 분석"):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 그룹 A")
                        cat1_a_dropdown = gr.Dropdown(label="대분류 A", choices=cat1_choices)
                        cat2_a_dropdown = gr.Dropdown(label="중분류 A", interactive=True)
                        cat3_a_dropdown = gr.Dropdown(label="소분류 A", interactive=True)
                    with gr.Column():
                        gr.Markdown("### 그룹 B")
                        cat1_b_dropdown = gr.Dropdown(label="대분류 B", choices=cat1_choices)
                        cat2_b_dropdown = gr.Dropdown(label="중분류 B", interactive=True)
                        cat3_b_dropdown = gr.Dropdown(label="소분류 B", interactive=True)
                
                with gr.Row():
                    compare_num_reviews = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="축제별 분석 리뷰 수")
                    compare_analyze_button = gr.Button("카테고리 비교 분석 시작", variant="primary")

                with gr.Row():
                    with gr.Column():
                        compare_status_output_a = gr.Textbox(label="분석 상태 A", interactive=False)
                        compare_combined_chart_a = gr.Plot(label="종합 분석 A")
                        compare_individual_charts_a = gr.Plot(label="개별 분석 A")
                    with gr.Column():
                        compare_status_output_b = gr.Textbox(label="분석 상태 B", interactive=False)
                        compare_combined_chart_b = gr.Plot(label="종합 분석 B")
                        compare_individual_charts_b = gr.Plot(label="개별 분석 B")

                # Dropdown 연동 로직 (A, B 그룹 모두에 적용)
                cat1_a_dropdown.change(update_cat2_choices, inputs=cat1_a_dropdown, outputs=cat2_a_dropdown)
                cat2_a_dropdown.change(update_cat3_choices, inputs=[cat1_a_dropdown, cat2_a_dropdown], outputs=cat3_a_dropdown)
                cat1_b_dropdown.change(update_cat2_choices, inputs=cat1_b_dropdown, outputs=cat2_b_dropdown)
                cat2_b_dropdown.change(update_cat3_choices, inputs=[cat1_b_dropdown, cat2_b_dropdown], outputs=cat3_b_dropdown)

                # 분석 버튼 클릭 이벤트
                compare_analyze_button.click(
                    compare_categories,
                    inputs=[cat1_a_dropdown, cat2_a_dropdown, cat3_a_dropdown, cat1_b_dropdown, cat2_b_dropdown, cat3_b_dropdown, compare_num_reviews],
                    outputs=[
                        compare_status_output_a, compare_combined_chart_a, compare_individual_charts_a,
                        compare_status_output_b, compare_combined_chart_b, compare_individual_charts_b
                    ]
                )

    return demo