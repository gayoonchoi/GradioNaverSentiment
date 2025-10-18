# src/presentation/ui_tabs.py
import gradio as gr
# 필요한 모듈 임포트 (상대 경로 주의)
from ..data import festival_loader
from .ui_components import create_keyword_analysis_outputs, create_category_analysis_outputs
from .event_handlers import update_cat2_choices, update_cat3_choices, update_festival_choices
# 서비스 함수 임포트 (상대 경로 주의)
from ..application.analysis_service import (
    analyze_keyword_and_generate_report,
    run_comparison_analysis,
    analyze_festivals_by_category,
    compare_categories,
    run_selected_festivals_comparison
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
            with gr.Column(scale=2):
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
            with gr.Column(scale=2):
                outputs = create_category_analysis_outputs()
        # 드롭다운 연동
        cat1_dd.change(update_cat2_choices, inputs=[cat1_dd], outputs=[cat2_dd]).then(
             lambda: gr.update(choices=[], value=None, interactive=False), outputs=[cat3_dd]
        )
        cat2_dd.change(update_cat3_choices, inputs=[cat1_dd, cat2_dd], outputs=[cat3_dd])
        # 분석 버튼 클릭
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
        # 드롭다운 연동 (그룹 A)
        cat1_a_dd.change(update_cat2_choices, inputs=[cat1_a_dd], outputs=[cat2_a_dd]).then(
            lambda: gr.update(choices=[], value=None, interactive=False), outputs=[cat3_a_dd]
        )
        cat2_a_dd.change(update_cat3_choices, inputs=[cat1_a_dd, cat2_a_dd], outputs=[cat3_a_dd])
        # 드롭다운 연동 (그룹 B)
        cat1_b_dd.change(update_cat2_choices, inputs=[cat1_b_dd], outputs=[cat2_b_dd]).then(
            lambda: gr.update(choices=[], value=None, interactive=False), outputs=[cat3_b_dd]
        )
        cat2_b_dd.change(update_cat3_choices, inputs=[cat1_b_dd, cat2_b_dd], outputs=[cat3_b_dd])
        # 분석 버튼 클릭
        analyze_button.click(
            compare_categories, 
            inputs=[cat1_a_dd, cat2_a_dd, cat3_a_dd, cat1_b_dd, cat2_b_dd, cat3_b_dd, num_reviews, log_details], 
            outputs=outputs_a + outputs_b
        )

def build_selected_festival_tab():
    """카테고리 선택 축제 비교 분석 탭 UI 생성"""
    cat1_choices = festival_loader.get_cat1_choices()
    with gr.TabItem("카테고리 선택 축제 비교 분석"):
        gr.Markdown("비교하고 싶은 축제를 최대 4개까지 선택하세요.")
        selected_festivals_inputs = [] 
        dropdown_groups = [] 

        with gr.Row():
            for i in range(4): 
                with gr.Column():
                    gr.Markdown(f"### 축제 {i+1}")
                    cat1_dd = gr.Dropdown(label="대분류", choices=cat1_choices, elem_id=f"sel_cat1_{i}")
                    cat2_dd = gr.Dropdown(label="중분류", interactive=False, elem_id=f"sel_cat2_{i}")
                    cat3_dd = gr.Dropdown(label="소분류", interactive=False, elem_id=f"sel_cat3_{i}")
                    festival_dd = gr.Dropdown(label="축제 선택", interactive=False, elem_id=f"sel_fest_{i}")
                    
                    selected_festivals_inputs.append(festival_dd)
                    dropdown_groups.append([cat1_dd, cat2_dd, cat3_dd, festival_dd])

                    # 각 그룹 내 드롭다운 연동 이벤트 설정
                    cat1_dd.change(update_cat2_choices, inputs=[cat1_dd], outputs=[cat2_dd]).then(
                        lambda: (gr.update(choices=[], value=None, interactive=False), gr.update(choices=[], value=None, interactive=False)), 
                        outputs=[cat3_dd, festival_dd]
                    )
                    cat2_dd.change(update_cat3_choices, inputs=[cat1_dd, cat2_dd], outputs=[cat3_dd]).then(
                         lambda: gr.update(choices=[], value=None, interactive=False), 
                         outputs=[festival_dd]
                    )
                    cat3_dd.change(update_festival_choices, inputs=[cat1_dd, cat2_dd, cat3_dd], outputs=[festival_dd])

        with gr.Row():
            num_reviews = gr.Slider(minimum=1, maximum=100, value=5, step=1, label="분석할 리뷰 수 (축제별)") 
            log_details = gr.Checkbox(label="상세 로그 출력", value=False) 
            analyze_button = gr.Button("선택 축제 비교 분석 시작", variant="primary") 
        
        selected_outputs_all = [] 
        with gr.Row():
            for i in range(4): 
                with gr.Column():
                    gr.Markdown(f"### 축제 {i+1} 분석 결과")
                    outputs_for_festival = create_keyword_analysis_outputs()
                    selected_outputs_all.extend(outputs_for_festival) 

        analyze_button.click(
            run_selected_festivals_comparison, 
            inputs=selected_festivals_inputs + [num_reviews, log_details], 
            outputs=selected_outputs_all
        )