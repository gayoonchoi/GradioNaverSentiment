# src/presentation/ui_tabs.py
import gradio as gr
from ..data import festival_loader
from .ui_components import create_keyword_analysis_outputs, create_category_analysis_outputs
from .event_handlers import update_cat2_choices, update_cat3_choices, update_festival_choices
from ..application.analysis_service import (
    analyze_keyword_and_generate_report,
    run_comparison_analysis,
    analyze_festivals_by_category,
    compare_categories,
    run_multi_group_comparison # 새로 만든 다중 그룹 비교 함수 임포트
)

def build_single_keyword_tab():
    """단일 키워드 분석 탭 UI 생성"""
    with gr.TabItem("단일 키워드 분석"):
        with gr.Row():
            with gr.Column(scale=1):
                keyword_input = gr.Textbox(label="검색어", placeholder="예: 제주도 핫플")
                num_reviews_input = gr.Slider(minimum=1, maximum=100, value=10, step=1, label="분석할 리뷰 수")
                log_details = gr.Checkbox(label="상세 로그 출력", value=False)
                analyze_button = gr.Button("분석 시작", variant="primary")
            with gr.Column(scale=3):
                outputs = create_keyword_analysis_outputs()
        analyze_button.click(
            analyze_keyword_and_generate_report, 
            inputs=[keyword_input, num_reviews_input, log_details], 
            outputs=outputs
        )

def build_keyword_comparison_tab():
    """키워드 비교 분석 탭 UI 생성"""
    with gr.TabItem("키워드 비교 분석"):
        with gr.Row():
            with gr.Column():
                keyword_input_a = gr.Textbox(label="키워드 A", placeholder="예: 제주도 핫플")
            with gr.Column():
                keyword_input_b = gr.Textbox(label="키워드 B", placeholder="예: 강릉 핫플")
        with gr.Row():
            num_reviews_comp = gr.Slider(minimum=1, maximum=100, value=10, step=1, label="분석할 리뷰 수 (키워드별)")
            log_details_comp = gr.Checkbox(label="상세 로그 출력", value=False)
            compare_button = gr.Button("키워드 비교 분석 시작", variant="primary")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 키워드 A 분석 결과")
                outputs_a = create_keyword_analysis_outputs()
            with gr.Column():
                gr.Markdown("### 키워드 B 분석 결과")
                outputs_b = create_keyword_analysis_outputs()
        compare_button.click(
            run_comparison_analysis, 
            inputs=[keyword_input_a, keyword_input_b, num_reviews_comp, log_details_comp], 
            outputs=outputs_a + outputs_b
        )

def build_category_analysis_tab():
    """카테고리별 축제 분석 탭 UI 생성"""
    cat1_choices = festival_loader.get_cat1_choices()
    with gr.TabItem("카테고리별 축제 분석"):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("분석하고 싶은 축제의 카테고리를 선택하세요.")
                cat1_dd = gr.Dropdown(label="대분류", choices=cat1_choices)
                cat2_dd = gr.Dropdown(label="중분류", interactive=False)
                cat3_dd = gr.Dropdown(label="소분류", interactive=False)
                num_reviews = gr.Slider(minimum=1, maximum=100, value=3, step=1, label="축제별 분석 리뷰 수")
                log_details = gr.Checkbox(label="상세 로그 출력", value=False)
                analyze_button = gr.Button("카테고리 분석 시작", variant="primary")
            with gr.Column(scale=3):
                outputs = create_category_analysis_outputs()
        cat1_dd.change(update_cat2_choices, inputs=[cat1_dd], outputs=[cat2_dd]).then(
             lambda: gr.update(choices=[], value=None, interactive=False), outputs=[cat3_dd]
        )
        cat2_dd.change(update_cat3_choices, inputs=[cat1_dd, cat2_dd], outputs=[cat3_dd])
        analyze_button.click(
            analyze_festivals_by_category, 
            inputs=[cat1_dd, cat2_dd, cat3_dd, num_reviews, log_details], 
            outputs=outputs
        )

def build_category_comparison_tab():
    """카테고리별 축제 비교 분석 탭 UI 생성"""
    cat1_choices = festival_loader.get_cat1_choices()
    with gr.TabItem("카테고리별 축제 비교 분석"):
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 그룹 A")
                cat1_a_dd = gr.Dropdown(label="대분류 A", choices=cat1_choices)
                cat2_a_dd = gr.Dropdown(label="중분류 A", interactive=False)
                cat3_a_dd = gr.Dropdown(label="소분류 A", interactive=False)
            with gr.Column():
                gr.Markdown("### 그룹 B")
                cat1_b_dd = gr.Dropdown(label="대분류 B", choices=cat1_choices)
                cat2_b_dd = gr.Dropdown(label="중분류 B", interactive=False)
                cat3_b_dd = gr.Dropdown(label="소분류 B", interactive=False)
        with gr.Row():
            num_reviews = gr.Slider(minimum=1, maximum=100, value=3, step=1, label="축제별 분석 리뷰 수")
            log_details = gr.Checkbox(label="상세 로그 출력", value=False)
            analyze_button = gr.Button("카테고리 비교 분석 시작", variant="primary")
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 그룹 A 분석 결과")
                outputs_a = create_category_analysis_outputs()
            with gr.Column():
                gr.Markdown("### 그룹 B 분석 결과")
                outputs_b = create_category_analysis_outputs()
        cat1_a_dd.change(update_cat2_choices, inputs=[cat1_a_dd], outputs=[cat2_a_dd]).then(
            lambda: gr.update(choices=[], value=None, interactive=False), outputs=[cat3_a_dd]
        )
        cat2_a_dd.change(update_cat3_choices, inputs=[cat1_a_dd, cat2_a_dd], outputs=[cat3_a_dd])
        cat1_b_dd.change(update_cat2_choices, inputs=[cat1_b_dd], outputs=[cat2_b_dd]).then(
            lambda: gr.update(choices=[], value=None, interactive=False), outputs=[cat3_b_dd]
        )
        cat2_b_dd.change(update_cat3_choices, inputs=[cat1_b_dd, cat2_b_dd], outputs=[cat3_b_dd])
        analyze_button.click(
            compare_categories, 
            inputs=[cat1_a_dd, cat2_a_dd, cat3_a_dd, cat1_b_dd, cat2_b_dd, cat3_b_dd, num_reviews, log_details], 
            outputs=outputs_a + outputs_b
        )

def build_custom_group_analysis_tab():
    """4개의 자율 그룹을 비교 분석하는 탭"""
    cat1_choices = festival_loader.get_cat1_choices()
    with gr.TabItem("자유 그룹 비교 분석"):
        gr.Markdown("비교하고 싶은 축제 그룹을 최대 4개까지 구성하여 분석합니다. 각 그룹은 카테고리 전체를 선택하거나, 축제를 직접 다중 선택할 수 있습니다.")
        
        all_inputs = []
        all_outputs = []

        with gr.Row():
            for i in range(4):
                with gr.Column():
                    gr.Markdown(f"### 그룹 {chr(ord('A') + i)}")
                    cat1_dd = gr.Dropdown(label="대분류", choices=cat1_choices)
                    cat2_dd = gr.Dropdown(label="중분류", interactive=False)
                    cat3_dd = gr.Dropdown(label="소분류", interactive=False)
                    festival_dd = gr.Dropdown(label="축제 직접 선택 (다중 선택 가능)", interactive=False, multiselect=True)
                    
                    all_inputs.extend([cat1_dd, cat2_dd, cat3_dd, festival_dd])

                    cat1_dd.change(update_cat2_choices, inputs=[cat1_dd], outputs=[cat2_dd]).then(
                        lambda: (gr.update(choices=[], value=None), gr.update(choices=[], value=None, interactive=False)), outputs=[cat3_dd, festival_dd]
                    )
                    cat2_dd.change(update_cat3_choices, inputs=[cat1_dd, cat2_dd], outputs=[cat3_dd]).then(
                        lambda: gr.update(choices=[], value=None, interactive=False), outputs=[festival_dd]
                    )
                    cat3_dd.change(update_festival_choices, inputs=[cat1_dd, cat2_dd, cat3_dd], outputs=[festival_dd])

        with gr.Row():
            num_reviews = gr.Slider(minimum=1, maximum=50, value=5, step=1, label="축제별 최대 분석 리뷰 수")
            log_details = gr.Checkbox(label="상세 로그 출력", value=False)
            analyze_button = gr.Button("자유 그룹 비교 분석 시작", variant="primary")
        
        with gr.Row():
            for i in range(4):
                with gr.Column():
                    gr.Markdown(f"### 그룹 {chr(ord('A') + i)} 분석 결과")
                    outputs = create_category_analysis_outputs()
                    all_outputs.extend(outputs)

        analyze_button.click(
            run_multi_group_comparison, 
            inputs=all_inputs + [num_reviews, log_details], 
            outputs=all_outputs
        )