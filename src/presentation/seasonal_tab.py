"""
계절별 인기 축제 탐색 탭 UI

사용자가 계절을 선택하면 해당 계절의 인기 축제를
워드클라우드, 타임라인 그래프, 테이블로 보여줍니다.
"""

import gradio as gr
from ..application import seasonal_analysis
from ..infrastructure.reporting import seasonal_wordcloud
from ..infrastructure.web.naver_trend_api import create_focused_trend_graph
from ..infrastructure.web.tour_api_client import get_festival_period


def analyze_seasonal_trends(season: str, progress=gr.Progress()):
    """
    계절별 인기 축제 분석 실행

    Args:
        season: 계절 ("봄", "여름", "가을", "겨울")

    Returns:
        tuple: (워드클라우드 이미지 경로, 타임라인 그래프 경로, 테이블 데이터프레임, 축제명 리스트, 상태 메시지)
    """
    if not season:
        return (
            None,
            None,
            None,
            gr.update(choices=[], value=None),
            "❌ 계절을 선택해주세요."
        )

    try:
        progress(0.1, desc="트렌드 데이터 로드 중...")

        # 1. 워드클라우드용 데이터 준비
        progress(0.3, desc="워드클라우드 생성 중...")
        freq_dict = seasonal_analysis.get_festival_frequency_dict(season, top_n=120)

        if not freq_dict:
            return (
                None,
                None,
                None,
                gr.update(choices=[], value=None),
                f"❌ {season} 시즌 데이터가 없습니다."
            )

        # 2. 워드클라우드 생성
        wordcloud_path = seasonal_wordcloud.create_wordcloud_for_gradio(freq_dict, season)

        # 3. 타임라인 그래프 생성
        progress(0.6, desc="타임라인 그래프 생성 중...")
        timeline_path = seasonal_analysis.create_timeline_graph(season, top_n=10)

        # 4. 테이블 데이터 준비
        progress(0.8, desc="테이블 데이터 준비 중...")
        table_df = seasonal_analysis.get_table_data(season, top_n=10)

        # 5. 축제명 리스트 (드롭다운용)
        festival_names = seasonal_analysis.get_festival_names_for_season(season, top_n=10)

        progress(1.0, desc="완료!")

        status_msg = f"✅ {season} 시즌 상위 10개 축제 분석 완료!"

        return (
            wordcloud_path,
            timeline_path,
            table_df,
            gr.update(choices=festival_names, value=None, visible=True),
            status_msg
        )

    except FileNotFoundError as e:
        return (
            None,
            None,
            None,
            gr.update(choices=[], value=None),
            f"❌ 데이터 파일이 없습니다.\n{str(e)}\n\nscripts/collect_all_trends.py를 먼저 실행해주세요."
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return (
            None,
            None,
            None,
            gr.update(choices=[], value=None),
            f"❌ 분석 중 오류 발생: {str(e)}"
        )


def show_festival_detail(festival_name: str):
    """
    선택된 축제의 상세 트렌드 표시

    Args:
        festival_name: 축제명

    Returns:
        tuple: (정보 메시지, 트렌드 그래프 경로, info_visible, img_visible)
    """
    if not festival_name:
        return (
            gr.update(visible=False),
            None,
            gr.update(visible=False)
        )

    try:
        # 축제 기간 가져오기
        start_date, end_date = get_festival_period(festival_name)

        # 트렌드 그래프 생성
        trend_graph_path, _ = create_focused_trend_graph(festival_name, start_date, end_date)

        info_msg = f"""
### 📊 {festival_name} 트렌드 분석

축제 기간: **{start_date or '정보 없음'}** ~ **{end_date or '정보 없음'}**

아래 그래프는 네이버 검색 트렌드를 기반으로 한 인기도 변화입니다.

💡 **더 자세한 분석을 원하시나요?**
"단일 키워드 분석" 탭으로 이동하여 **"{festival_name}"**를 검색하면
블로그 감성 분석, 키워드 추출, 워드클라우드 등 심층 분석이 가능합니다!
        """

        return (
            gr.update(value=info_msg, visible=True),
            trend_graph_path,
            gr.update(visible=True)
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        return (
            gr.update(value=f"❌ 트렌드 데이터 로드 실패: {str(e)}", visible=True),
            None,
            gr.update(visible=False)
        )


def build_seasonal_trend_tab():
    """계절별 인기 축제 탐색 탭 UI 빌드"""
    with gr.TabItem("계절별 인기 축제 탐색"):
        gr.Markdown("""
        ## 🎪 계절별 인기 축제 탐색

        **네이버 검색 트렌드**를 기반으로 각 계절별로 가장 인기있는 축제를 발견하세요!

        - 📊 **워드클라우드**: 검색량이 많을수록 크게 표시됩니다
        - 📅 **타임라인**: 축제 기간과 검색량을 한눈에 확인
        - 🔍 **상세 분석**: 흥미로운 축제를 선택하여 더 깊이 분석할 수 있습니다
        """)

        with gr.Row():
            with gr.Column(scale=1):
                # STEP 1: 계절 선택
                gr.Markdown("### STEP 1: 계절 선택")
                season_radio = gr.Radio(
                    choices=["봄", "여름", "가을", "겨울"],
                    label="분석할 계절을 선택하세요",
                    value="봄"
                )
                analyze_btn = gr.Button("🔍 분석 시작", variant="primary", size="lg")

                # 상태 메시지
                status_msg = gr.Textbox(
                    label="상태",
                    interactive=False,
                    lines=3
                )

                gr.Markdown("---")

                # STEP 3: 상세 분석
                gr.Markdown("### STEP 3: 축제 상세 분석")
                gr.Markdown("테이블에서 흥미로운 축제를 발견하셨나요?\n아래에서 선택하여 더 깊이 분석해보세요!")

                festival_dropdown = gr.Dropdown(
                    label="분석할 축제 선택",
                    choices=[],
                    visible=False
                )
                detail_analyze_btn = gr.Button(
                    "📊 이 축제 트렌드 보기",
                    variant="secondary",
                    visible=False
                )
                detail_info = gr.Markdown(visible=False)
                detail_trend_img = gr.Image(
                    label="축제 트렌드 그래프",
                    type="filepath",
                    visible=False
                )
                gr.Markdown("""
                > **💡 Tip**: 더 자세한 블로그 감성 분석을 원하시면
                > **"단일 키워드 분석"** 탭으로 이동하여
                > 선택한 축제명을 검색해보세요!
                """)

            with gr.Column(scale=3):
                # STEP 2: 분석 결과
                gr.Markdown("### STEP 2: 분석 결과")

                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 📊 워드클라우드")
                        wordcloud_img = gr.Image(
                            label="계절별 인기 축제 워드클라우드",
                            type="filepath"
                        )

                    with gr.Column():
                        gr.Markdown("#### 📅 축제 기간 타임라인")
                        timeline_img = gr.Image(
                            label="상위 10개 축제 타임라인",
                            type="filepath"
                        )

                gr.Markdown("#### 📋 상위 10개 축제 상세 정보")
                table_output = gr.Dataframe(
                    headers=["순위", "축제명", "최대 검색량", "평균 검색량", "행사 시작일", "행사 종료일"],
                    label="상위 10개 인기 축제",
                    interactive=False,
                    wrap=True
                )

        # 이벤트 핸들러
        analyze_btn.click(
            analyze_seasonal_trends,
            inputs=[season_radio],
            outputs=[wordcloud_img, timeline_img, table_output, festival_dropdown, status_msg]
        ).then(
            lambda: (gr.update(visible=True), gr.update(visible=True)),
            outputs=[festival_dropdown, detail_analyze_btn]
        )

        # 상세 분석 버튼 클릭 이벤트
        detail_analyze_btn.click(
            show_festival_detail,
            inputs=[festival_dropdown],
            outputs=[detail_info, detail_trend_img, detail_trend_img]
        )

        return {
            'festival_dropdown': festival_dropdown,
            'detail_analyze_btn': detail_analyze_btn
        }
