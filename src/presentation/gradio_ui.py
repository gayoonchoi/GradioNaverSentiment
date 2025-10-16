import gradio as gr
from src.application.analysis_service import analyze_keyword_and_generate_report, run_comparison_analysis, change_page

def create_ui():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("## 🚀 LLM 우선 네이버 블로그 감성 분석기")

        # State to hold the full dataframe for pagination
        full_df_state = gr.State()
        full_df_state_a = gr.State()
        full_df_state_b = gr.State()

        with gr.Tabs():
            with gr.TabItem("단일 키워드 분석"):
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
                        results_output, # Paginated results
                        url_output,
                        full_df_state, # Full results for state
                        page_num_input,
                        total_pages_output,
                        negative_summary_output,
                        negative_download_output
                    ]
                )

            with gr.TabItem("키워드 비교 분석"):
                gr.Markdown("비교 분석 기능은 현재 비활성화되어 있습니다. 단일 키워드 분석을 이용해주세요.")

    return demo