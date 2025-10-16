import gradio as gr
import pandas as pd
from src.application.analysis_service import (
    analyze_festivals_by_category,
    compare_categories,
    change_page
)
from src.data import festival_loader

def create_ui():
    cat1_choices = festival_loader.get_cat1_choices()

    def create_category_analysis_outputs():
        """카테고리 분석 결과 UI 컴포넌트 그룹을 생성합니다."""
        with gr.Blocks():
            status_output = gr.Textbox(label="분석 상태", interactive=False)
            with gr.Accordion("종합 분석 결과", open=False):
                negative_summary_output = gr.Markdown(label="주요 불만 사항 요약", visible=False)
                negative_download_output = gr.File(label="부정적 의견 요약(CSV) 다운로드", visible=False)
                overall_chart_output = gr.Plot(label="전체 후기 요약", visible=False)
                with gr.Row():
                    spring_chart_output = gr.Plot(label="봄 시즌", visible=False)
                    summer_chart_output = gr.Plot(label="여름 시즌", visible=False)
                with gr.Row():
                    autumn_chart_output = gr.Plot(label="가을 시즌", visible=False)
                    winter_chart_output = gr.Plot(label="겨울 시즌", visible=False)
            
            gr.Markdown("### 축제별 개별 분석 결과")
            individual_results_df = gr.State() # 전체 데이터프레임 상태
            individual_results_output = gr.DataFrame(headers=["축제명", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)"], label="축제별 분석 결과", wrap=True)
            with gr.Row():
                page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True)
                total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False)
            
            page_num_input.submit(change_page, inputs=[individual_results_df, page_num_input], outputs=[individual_results_output, page_num_input, total_pages_output])

        outputs = [
            status_output, negative_summary_output, negative_download_output, 
            overall_chart_output, spring_chart_output, summer_chart_output, autumn_chart_output, winter_chart_output,
            individual_results_output, individual_results_df, page_num_input, total_pages_output
        ]
        return outputs

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
                        log_checkbox = gr.Checkbox(label="상세 로그 출력", value=False)
                        category_num_reviews = gr.Slider(minimum=1, maximum=10, value=3, step=1, label="축제별 분석 리뷰 수")
                        category_analyze_button = gr.Button("카테고리 분석 시작", variant="primary")
                    with gr.Column(scale=2):
                        # UI 컴포넌트 생성 및 반환
                        category_outputs = create_category_analysis_outputs()

                # Dropdown 연동 로직
                def update_cat2_choices(cat1):
                    return gr.update(choices=festival_loader.get_cat2_choices(cat1), value=None)
                def update_cat3_choices(cat1, cat2):
                    return gr.update(choices=festival_loader.get_cat3_choices(cat1, cat2), value=None)

                cat1_dropdown.change(update_cat2_choices, inputs=cat1_dropdown, outputs=cat2_dropdown)
                cat2_dropdown.change(update_cat3_choices, inputs=[cat1_dropdown, cat2_dropdown], outputs=cat3_dropdown)

                category_analyze_button.click(
                    analyze_festivals_by_category,
                    inputs=[cat1_dropdown, cat2_dropdown, cat3_dropdown, category_num_reviews, log_checkbox],
                    outputs=category_outputs
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
                    compare_log_checkbox = gr.Checkbox(label="상세 로그 출력", value=False)
                    compare_analyze_button = gr.Button("카테고리 비교 분석 시작", variant="primary")

                with gr.Row():
                    with gr.Column():
                        compare_outputs_a = create_category_analysis_outputs()
                    with gr.Column():
                        compare_outputs_b = create_category_analysis_outputs()

                # Dropdown 연동 로직 (A, B 그룹)
                cat1_a_dropdown.change(update_cat2_choices, inputs=cat1_a_dropdown, outputs=cat2_a_dropdown)
                cat2_a_dropdown.change(update_cat3_choices, inputs=[cat1_a_dropdown, cat2_a_dropdown], outputs=cat3_a_dropdown)
                cat1_b_dropdown.change(update_cat2_choices, inputs=cat1_b_dropdown, outputs=cat2_b_dropdown)
                cat2_b_dropdown.change(update_cat3_choices, inputs=[cat1_b_dropdown, cat2_b_dropdown], outputs=cat3_b_dropdown)

                compare_analyze_button.click(
                    compare_categories,
                    inputs=[cat1_a_dropdown, cat2_a_dropdown, cat3_a_dropdown, cat1_b_dropdown, cat2_b_dropdown, cat3_b_dropdown, compare_num_reviews, compare_log_checkbox],
                    outputs=compare_outputs_a + compare_outputs_b
                )

            # 비활성화된 탭들
            with gr.TabItem("단일 키워드 분석"):
                gr.Markdown("이 기능은 현재 비활성화되었습니다. 카테고리별 분석 기능을 이용해주세요.")
            with gr.TabItem("키워드 비교 분석"):
                gr.Markdown("이 기능은 현재 비활성화되었습니다. 카테고리별 비교 분석 기능을 이용해주세요.")

    return demo