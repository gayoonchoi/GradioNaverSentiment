# src/presentation/gradio_ui.py
import gradio as gr
# 탭 빌더 함수 임포트
from .ui_tabs import (
    build_single_keyword_tab,
    build_keyword_comparison_tab,
    build_category_analysis_tab,
    build_category_comparison_tab,
    build_custom_group_analysis_tab,
    build_seasonal_trend_tab  # 새로운 계절별 탭
)

def create_ui():
    """메인 Gradio UI 생성"""
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("## 🚀 LLM 우선 네이버 블로그 감성 분석기")

        with gr.Tabs():
            # 각 탭 빌더 함수 호출
            build_single_keyword_tab()
            build_keyword_comparison_tab()
            build_category_analysis_tab()
            build_category_comparison_tab()
            build_custom_group_analysis_tab()
            build_seasonal_trend_tab()  # 계절별 인기 축제 탐색 탭 추가

    return demo