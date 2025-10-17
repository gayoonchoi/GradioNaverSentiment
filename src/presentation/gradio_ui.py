import gradio as gr
import pandas as pd
from src.application.analysis_service import (
    analyze_keyword_and_generate_report,
    run_comparison_analysis,
    analyze_festivals_by_category,
    compare_categories,
    change_page,
    package_festival_details
)
from src.data import festival_loader
from src.infrastructure.reporting.charts import create_donut_chart, create_sentence_score_bar_chart

def create_ui():
    cat1_choices = festival_loader.get_cat1_choices()

    # --- Event Handlers ---

    # [수정] 모든 블로그 표 클릭을 처리하는 통합 핸들러
    # 페이지네이션을 고려하여 실제 인덱스를 계산하고, Accordion을 포함한 4개 출력을 반환
    def update_individual_charts(evt: gr.SelectData, df_full: pd.DataFrame, judgments_list: list, page_num: int):
        if not evt.value or not judgments_list:
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

        PAGE_SIZE = 10
        # 페이지 번호와 클릭 위치를 조합하여 전체 데이터에서의 실제 인덱스 계산
        actual_index = (int(page_num) - 1) * PAGE_SIZE + evt.index[0]

        if actual_index >= len(df_full):
            return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

        selected_row = df_full.iloc[actual_index]
        blog_title = selected_row["블로그 제목"]
        pos_count = selected_row["긍정 문장 수"]
        neg_count = selected_row["부정 문장 수"]
        summary_text = selected_row["긍/부정 문장 요약"].replace('*', '').replace('---', '')
        judgments = judgments_list[actual_index]
        
        score_chart = create_sentence_score_bar_chart(judgments, f'{blog_title[:20]}... 문장별 점수')
        donut_chart = create_donut_chart(pos_count, neg_count, f'{blog_title[:20]}... 긍/부정 비율')
        
        # Accordion을 열어주는 4번째 반환값 추가
        return gr.update(value=donut_chart, visible=True), gr.update(value=score_chart, visible=True), gr.update(value=summary_text, visible=True), gr.update(open=True, visible=True)

    # [수정] 축제 표 클릭 핸들러에도 페이지네이션 인덱스 계산 로직 추가
    def update_festival_detail_charts(evt: gr.SelectData, df_full: pd.DataFrame, festival_full_results: list, page_num: int):
        if not evt.value or not festival_full_results:
            return [gr.update(visible=False)] * 8

        PAGE_SIZE = 10
        actual_index = (int(page_num) - 1) * PAGE_SIZE + evt.index[0]
        
        if actual_index >= len(df_full):
            return [gr.update(visible=False)] * 8

        selected_row = df_full.iloc[actual_index]
        festival_name = selected_row["축제명"]
        selected_festival_result = festival_full_results[actual_index]
        
        return package_festival_details(selected_festival_result, festival_name)

    # --- UI Component Creators ---
    def create_keyword_analysis_outputs():
        with gr.Blocks():
            status_output = gr.Textbox(label="분석 상태", interactive=False)
            url_output = gr.Markdown(label="수집된 전체 URL 리스트")
            with gr.Accordion("종합 분석 결과", open=True):
                negative_summary_output = gr.Markdown(label="주요 불만 사항 요약", visible=False)
                with gr.Row():
                    overall_chart_output = gr.Plot(label="전체 후기 요약", visible=False)
                    overall_summary_text_output = gr.Markdown(label="종합 분석 상세", visible=False)
                    overall_csv_output = gr.File(label="전체 후기 요약 (CSV) 다운로드", visible=False)
                with gr.Accordion("계절별 상세 분석", open=False):
                    with gr.Row():
                        spring_chart_output = gr.Plot(label="봄 시즌", visible=False)
                        summer_chart_output = gr.Plot(label="여름 시즌", visible=False)
                    with gr.Row():
                        autumn_chart_output = gr.Plot(label="가을 시즌", visible=False)
                        winter_chart_output = gr.Plot(label="겨울 시즌", visible=False)
            
            gr.Markdown("### 개별 블로그 분석 결과")
            blog_results_df = gr.State()
            blog_judgments_state = gr.State()
            blog_results_output = gr.DataFrame(headers=["블로그 제목", "링크", "감성 빈도", "감성 점수", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)", "부정 비율 (%)"], label="개별 블로그 분석 결과", wrap=True, interactive=True)
            with gr.Row():
                blog_page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True, scale=1)
                blog_total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False, scale=1)
                blog_list_csv_output = gr.File(label="전체 블로그 목록(CSV) 다운로드", visible=False, scale=2)
            
            with gr.Accordion("개별 블로그 상세 분석 (표에서 행 선택)", open=False, visible=True) as blog_detail_accordion:
                individual_summary_output = gr.Textbox(label="긍/부정 문장 요약", visible=False, interactive=False, lines=10)
                with gr.Row():
                    individual_donut_chart = gr.Plot(label="개별 블로그 긍/부정 비율", visible=False)
                    individual_score_chart = gr.Plot(label="문장별 감성 점수", visible=False)

            blog_page_num_input.submit(change_page, inputs=[blog_results_df, blog_page_num_input], outputs=[blog_results_output, blog_page_num_input, blog_total_pages_output])
            
            # [수정] 이벤트 연결부에 페이지 번호(blog_page_num_input)를 전달하고, 출력 개수를 4개로 맞춤
            blog_results_output.select(
                update_individual_charts, 
                inputs=[blog_results_df, blog_judgments_state, blog_page_num_input], 
                outputs=[individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion]
            )

        return [
            status_output, url_output, negative_summary_output,
            overall_chart_output, overall_summary_text_output, overall_csv_output,
            spring_chart_output, summer_chart_output, autumn_chart_output, winter_chart_output,
            blog_results_output, blog_results_df, blog_judgments_state, blog_page_num_input, blog_total_pages_output, blog_list_csv_output,
            individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion
        ]

    def create_category_analysis_outputs():
        with gr.Blocks():
            status_output = gr.Textbox(label="분석 상태", interactive=False)
            with gr.Accordion("카테고리 종합 분석 결과", open=True):
                cat_negative_summary_output = gr.Markdown(label="주요 불만 사항 요약", visible=False)
                with gr.Row():
                    cat_overall_chart_output = gr.Plot(label="카테고리 전체 후기 요약", visible=False)
                    cat_overall_summary_text_output = gr.Markdown(label="종합 분석 상세", visible=False)
                    cat_overall_csv_output = gr.File(label="카테고리 전체 요약 (CSV) 다운로드", visible=False)
                with gr.Accordion("계절별 상세 분석", open=False):
                    with gr.Row():
                        cat_spring_chart_output = gr.Plot(label="봄 시즌", visible=False)
                        cat_summer_chart_output = gr.Plot(label="여름 시즌", visible=False)
                    with gr.Row():
                        cat_autumn_chart_output = gr.Plot(label="가을 시즌", visible=False)
                        cat_winter_chart_output = gr.Plot(label="겨울 시즌", visible=False)

            gr.Markdown("### 축제별 요약 결과")
            festival_results_df = gr.State()
            festival_full_results_state = gr.State()
            festival_results_output = gr.DataFrame(headers=["축제명", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)"], label="축제별 분석 결과", wrap=True, interactive=True)
            with gr.Row():
                festival_page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True, scale=1)
                festival_total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False, scale=1)
                festival_list_csv_output = gr.File(label="축제 요약 목록(CSV) 다운로드", visible=False, scale=2)

            with gr.Accordion("개별 축제 상세 분석 (표에서 행 선택)", open=False, visible=False) as festival_detail_accordion:
                fest_negative_summary_output = gr.Markdown(label="주요 불만 사항 요약", visible=False)
                with gr.Row():
                    fest_overall_chart_output = gr.Plot(label="개별 축제 후기 요약", visible=False)
                    fest_overall_summary_text_output = gr.Markdown(label="종합 분석 상세", visible=False)
                with gr.Accordion("계절별 상세 분석", open=False):
                    with gr.Row():
                        fest_spring_chart_output = gr.Plot(label="봄 시즌", visible=False)
                        fest_summer_chart_output = gr.Plot(label="여름 시즌", visible=False)
                    with gr.Row():
                        fest_autumn_chart_output = gr.Plot(label="가을 시즌", visible=False)
                        fest_winter_chart_output = gr.Plot(label="겨울 시즌", visible=False)

            gr.Markdown("### 전체 블로그 상세 결과")
            all_blogs_df = gr.State()
            all_blog_judgments_state = gr.State()
            all_blogs_output = gr.DataFrame(headers=["블로그 제목", "링크", "감성 빈도", "감성 점수", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)", "부정 비율 (%)"], label="전체 블로그 분석 결과", wrap=True, interactive=True)
            with gr.Row():
                all_blogs_page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True, scale=1)
                all_blogs_total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False, scale=1)
                all_blogs_list_csv_output = gr.File(label="전체 블로그 목록(CSV) 다운로드", visible=False, scale=2)

            with gr.Accordion("개별 블로그 상세 분석 (표에서 행 선택)", open=False, visible=False) as blog_detail_accordion:
                individual_summary_output = gr.Textbox(label="긍/부정 문장 요약", visible=False, interactive=False, lines=10)
                with gr.Row():
                    individual_donut_chart = gr.Plot(label="개별 블로그 긍/부정 비율", visible=False)
                    individual_score_chart = gr.Plot(label="문장별 감성 점수", visible=False)

            festival_page_num_input.submit(change_page, inputs=[festival_results_df, festival_page_num_input], outputs=[festival_results_output, festival_page_num_input, festival_total_pages_output])
            all_blogs_page_num_input.submit(change_page, inputs=[all_blogs_df, all_blogs_page_num_input], outputs=[all_blogs_output, all_blogs_page_num_input, all_blogs_total_pages_output])
            
            festival_detail_outputs = [
                fest_negative_summary_output, fest_overall_chart_output, fest_overall_summary_text_output,
                fest_spring_chart_output, fest_summer_chart_output, fest_autumn_chart_output, fest_winter_chart_output, festival_detail_accordion
            ]
            # [수정] 축제 표 클릭 이벤트에도 페이지 번호(festival_page_num_input)를 전달
            festival_results_output.select(
                update_festival_detail_charts, 
                inputs=[festival_results_df, festival_full_results_state, festival_page_num_input], 
                outputs=festival_detail_outputs
            )
            
            blog_detail_outputs = [individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion]
            # [수정] 블로그 표 클릭 이벤트에도 페이지 번호(all_blogs_page_num_input)를 전달
            all_blogs_output.select(
                update_individual_charts, 
                inputs=[all_blogs_df, all_blog_judgments_state, all_blogs_page_num_input], 
                outputs=blog_detail_outputs
            )

        return [
            status_output, cat_negative_summary_output, cat_overall_chart_output, cat_overall_summary_text_output, cat_overall_csv_output,
            cat_spring_chart_output, cat_summer_chart_output, cat_autumn_chart_output, cat_winter_chart_output,
            festival_results_output, festival_results_df, festival_full_results_state, festival_page_num_input, festival_total_pages_output, festival_list_csv_output,
            fest_negative_summary_output, fest_overall_chart_output, fest_overall_summary_text_output,
            fest_spring_chart_output, fest_summer_chart_output, fest_autumn_chart_output, fest_winter_chart_output, festival_detail_accordion,
            all_blogs_output, all_blogs_df, all_blog_judgments_state, all_blogs_page_num_input, all_blogs_total_pages_output, all_blogs_list_csv_output,
            individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion
        ]

    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("## 🚀 LLM 우선 네이버 블로그 감성 분석기")
        with gr.Tabs():
            with gr.TabItem("단일 키워드 분석"):
                with gr.Row():
                    with gr.Column(scale=1):
                        keyword_input = gr.Textbox(label="검색어", placeholder="예: 제주도 핫플")
                        num_reviews_input = gr.Slider(minimum=1, maximum=100, value=10, step=1, label="분석할 리뷰 수")
                        log_details_keyword = gr.Checkbox(label="상세 로그 출력", value=False)
                        analyze_button = gr.Button("분석 시작", variant="primary")
                    with gr.Column(scale=2):
                        keyword_outputs = create_keyword_analysis_outputs()
                analyze_button.click(analyze_keyword_and_generate_report, inputs=[keyword_input, num_reviews_input, log_details_keyword], outputs=keyword_outputs)

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
                        keyword_outputs_a = create_keyword_analysis_outputs()
                    with gr.Column():
                        gr.Markdown("### 키워드 B 분석 결과")
                        keyword_outputs_b = create_keyword_analysis_outputs()
                compare_button.click(run_comparison_analysis, inputs=[keyword_input_a, keyword_input_b, num_reviews_comp, log_details_comp], outputs=keyword_outputs_a + keyword_outputs_b)

            with gr.TabItem("카테고리별 축제 분석"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("분석하고 싶은 축제의 카테고리를 선택하세요.")
                        cat1_dropdown = gr.Dropdown(label="대분류", choices=cat1_choices)
                        cat2_dropdown = gr.Dropdown(label="중분류", interactive=True)
                        cat3_dropdown = gr.Dropdown(label="소분류", interactive=True)
                        category_num_reviews = gr.Slider(minimum=1, maximum=100, value=3, step=1, label="축제별 분석 리뷰 수")
                        log_details_cat = gr.Checkbox(label="상세 로그 출력", value=False)
                        category_analyze_button = gr.Button("카테고리 분석 시작", variant="primary")
                    with gr.Column(scale=2):
                        category_outputs = create_category_analysis_outputs()
                def update_cat2_choices(cat1): return gr.update(choices=festival_loader.get_cat2_choices(cat1), value=None)
                def update_cat3_choices(cat1, cat2): return gr.update(choices=festival_loader.get_cat3_choices(cat1, cat2), value=None)
                cat1_dropdown.change(update_cat2_choices, inputs=cat1_dropdown, outputs=cat2_dropdown)
                cat2_dropdown.change(update_cat3_choices, inputs=[cat1_dropdown, cat2_dropdown], outputs=cat3_dropdown)
                category_analyze_button.click(analyze_festivals_by_category, inputs=[cat1_dropdown, cat2_dropdown, cat3_dropdown, category_num_reviews, log_details_cat], outputs=category_outputs)

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
                    compare_num_reviews = gr.Slider(minimum=1, maximum=100, value=3, step=1, label="축제별 분석 리뷰 수")
                    compare_log_checkbox = gr.Checkbox(label="상세 로그 출력", value=False)
                    compare_analyze_button = gr.Button("카테고리 비교 분석 시작", variant="primary")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 그룹 A 분석 결과")
                        compare_outputs_a = create_category_analysis_outputs()
                    with gr.Column():
                        gr.Markdown("### 그룹 B 분석 결과")
                        compare_outputs_b = create_category_analysis_outputs()
                cat1_a_dropdown.change(update_cat2_choices, inputs=cat1_a_dropdown, outputs=cat2_a_dropdown)
                cat2_a_dropdown.change(update_cat3_choices, inputs=[cat1_a_dropdown, cat2_a_dropdown], outputs=cat3_a_dropdown)
                cat1_b_dropdown.change(update_cat2_choices, inputs=cat1_b_dropdown, outputs=cat2_b_dropdown)
                cat2_b_dropdown.change(update_cat3_choices, inputs=[cat1_b_dropdown, cat2_b_dropdown], outputs=cat3_b_dropdown)
                compare_analyze_button.click(compare_categories, inputs=[cat1_a_dropdown, cat2_a_dropdown, cat3_a_dropdown, cat1_b_dropdown, cat2_b_dropdown, cat3_b_dropdown, compare_num_reviews, compare_log_checkbox], outputs=compare_outputs_a + compare_outputs_b)

    return demo