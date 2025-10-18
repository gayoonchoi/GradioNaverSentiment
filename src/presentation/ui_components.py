# src/presentation/ui_components.py
import gradio as gr
# 이벤트 핸들러 임포트 (상대 경로 주의)
from .event_handlers import update_individual_charts, change_page, update_festival_detail_charts # update_festival_detail_charts 추가

def create_keyword_analysis_outputs():
    """단일 키워드 분석 결과 UI 컴포넌트 그룹 생성"""
    with gr.Blocks():
        status_output = gr.Textbox(label="분석 상태", interactive=False)
        url_output = gr.Markdown(label="수집된 전체 URL 리스트")
        with gr.Accordion("종합 분석 결과", open=True):
            negative_summary_output = gr.Markdown(label="주요 불만 사항 요약", visible=False)
            with gr.Row():
                overall_chart_output = gr.Plot(label="전체 후기 요약", visible=False)
                trend_graph_output = gr.Image(label="검색어 트렌드", visible=False)
            with gr.Row():
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
        blog_results_df = gr.State() # 전체 데이터 저장용
        blog_judgments_state = gr.State() # 전체 judgments 저장용
        blog_results_output = gr.DataFrame( # 현재 페이지만 표시
            headers=["블로그 제목", "링크", "감성 빈도", "감성 점수", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)", "부정 비율 (%)", "긍/부정 문장 요약"],
            datatype=["str", "str", "number", "str", "number", "number", "str", "str", "str"],
            label="개별 블로그 분석 결과", wrap=True, interactive=True
        )
        with gr.Row():
            blog_page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True, scale=1)
            blog_total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False, scale=1)
            blog_list_csv_output = gr.File(label="전체 블로그 목록(CSV) 다운로드", visible=False, scale=2)

        with gr.Accordion("개별 블로그 상세 분석 (표에서 행 선택)", open=False, visible=True) as blog_detail_accordion:
            individual_summary_output = gr.Textbox(label="긍/부정 문장 요약", visible=False, interactive=False, lines=10) # 상세 보기는 Textbox
            with gr.Row():
                individual_donut_chart = gr.Plot(label="개별 블로그 긍/부정 비율", visible=False)
                individual_score_chart = gr.Plot(label="문장별 감성 점수", visible=False)

        # 페이지네이션 이벤트
        blog_page_num_input.submit(
            change_page,
            inputs=[blog_results_df, blog_page_num_input],
            outputs=[blog_results_output, blog_page_num_input, blog_total_pages_output]
        )

        # 표 클릭 이벤트
        blog_results_output.select(
            update_individual_charts,
            inputs=[blog_results_df, blog_judgments_state, blog_page_num_input],
            outputs=[individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion]
        )

    # UI 컴포넌트 리스트 반환 (순서 중요!) - 총 21개
    return [
        status_output, url_output, negative_summary_output,
        overall_chart_output, trend_graph_output, overall_summary_text_output, overall_csv_output,
        spring_chart_output, summer_chart_output, autumn_chart_output, winter_chart_output,
        blog_results_output, blog_results_df, blog_judgments_state, blog_page_num_input, blog_total_pages_output, blog_list_csv_output,
        individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion
    ]


def create_category_analysis_outputs():
    """카테고리 분석 결과 UI 컴포넌트 그룹 생성"""

    with gr.Blocks():
        # Tier 1: 카테고리 종합 분석
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

        # Tier 2: 축제별 요약 및 상세 분석
        gr.Markdown("### 축제별 요약 결과")
        festival_results_df = gr.State() # 전체 축제 데이터 저장
        festival_full_results_state = gr.State() # 축제별 상세 결과 저장
        festival_results_output = gr.DataFrame( # 현재 페이지만 표시
            headers=["축제명", "감성 빈도", "감성 점수", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)", "부정 비율 (%)", "주요 불만 사항 요약"],
            datatype=["str", "number", "str", "number", "number", "str", "str", "str"],
            label="축제별 분석 결과", wrap=True, interactive=True
        )
        with gr.Row():
            festival_page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True, scale=1)
            festival_total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False, scale=1)
            festival_list_csv_output = gr.File(label="축제 요약 목록(CSV) 다운로드", visible=False, scale=2)

        with gr.Accordion("개별 축제 상세 분석 (표에서 행 선택)", open=False, visible=False) as festival_detail_accordion:
            fest_trend_graph_output = gr.Image(label="검색어 트렌드", visible=False)
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

        # Tier 3: 전체 블로그 상세 결과 및 개별 블로그 상세 분석
        gr.Markdown("### 전체 블로그 상세 결과")
        all_blogs_df = gr.State() # State에는 '긍/부정 요약'이 *포함된* 전체 DF가 와야 함!
        all_blog_judgments_state = gr.State() # 전체 블로그 judgments 저장
        all_blogs_output = gr.DataFrame( # 현재 페이지만 표시
            headers=["블로그 제목", "링크", "감성 빈도", "감성 점수", "긍정 문장 수", "부정 문장 수", "긍정 비율 (%)", "부정 비율 (%)", "긍/부정 문장 요약"],
            datatype=["str", "str", "number", "str", "number", "number", "str", "str", "str"],
            label="전체 블로그 분석 결과", wrap=True, interactive=True
        )
        with gr.Row():
            all_blogs_page_num_input = gr.Number(value=1, label="페이지 번호", interactive=True, scale=1)
            all_blogs_total_pages_output = gr.Textbox(value="/ 1", label="전체 페이지", interactive=False, scale=1)
            all_blogs_list_csv_output = gr.File(label="전체 블로그 목록(CSV) 다운로드", visible=False, scale=2)

        with gr.Accordion("개별 블로그 상세 분석 (표에서 행 선택)", open=False, visible=False) as blog_detail_accordion:
            individual_summary_output = gr.Textbox(label="긍/부정 문장 요약", visible=False, interactive=False, lines=10) # 상세 보기는 Textbox
            with gr.Row():
                individual_donut_chart = gr.Plot(label="개별 블로그 긍/부정 비율", visible=False)
                individual_score_chart = gr.Plot(label="문장별 감성 점수", visible=False)

        # --- Event Handlers for Category Tab ---
        festival_page_num_input.submit(
            change_page,
            inputs=[festival_results_df, festival_page_num_input],
            outputs=[festival_results_output, festival_page_num_input, festival_total_pages_output]
        )
        all_blogs_page_num_input.submit(
            change_page,
            inputs=[all_blogs_df, all_blogs_page_num_input],
            outputs=[all_blogs_output, all_blogs_page_num_input, all_blogs_total_pages_output]
        )

        festival_detail_outputs = [
            fest_trend_graph_output,
            fest_negative_summary_output, fest_overall_chart_output, fest_overall_summary_text_output,
            fest_spring_chart_output, fest_summer_chart_output, fest_autumn_chart_output, fest_winter_chart_output,
            festival_detail_accordion
        ]
        festival_results_output.select(
            update_festival_detail_charts,
            inputs=[festival_results_df, festival_full_results_state, festival_page_num_input],
            outputs=festival_detail_outputs
        )

        blog_detail_outputs = [
            individual_donut_chart, individual_score_chart, individual_summary_output,
            blog_detail_accordion
        ]
        all_blogs_output.select(
            update_individual_charts,
            inputs=[all_blogs_df, all_blog_judgments_state, all_blogs_page_num_input],
            outputs=blog_detail_outputs
        )

    # --- 핵심 수정: 반환 리스트의 개수를 34개로 정확히 맞춤 ---
    return [
        # Tier 1 (9개)
        status_output, cat_negative_summary_output, cat_overall_chart_output, cat_overall_summary_text_output, cat_overall_csv_output,
        cat_spring_chart_output, cat_summer_chart_output, cat_autumn_chart_output, cat_winter_chart_output,
        # Tier 2 (15개)
        festival_results_output, festival_results_df, festival_full_results_state, festival_page_num_input, festival_total_pages_output, festival_list_csv_output,
        fest_trend_graph_output, fest_negative_summary_output, fest_overall_chart_output, fest_overall_summary_text_output,
        fest_spring_chart_output, fest_summer_chart_output, fest_autumn_chart_output, fest_winter_chart_output, festival_detail_accordion,
        # Tier 3 (10개)
        all_blogs_output, all_blogs_df, all_blog_judgments_state, all_blogs_page_num_input, all_blogs_total_pages_output, all_blogs_list_csv_output,
        individual_donut_chart, individual_score_chart, individual_summary_output, blog_detail_accordion
    ]