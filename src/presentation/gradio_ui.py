# src/presentation/gradio_ui.py
import gradio as gr
# 탭 빌더 함수 임포트
from .ui_tabs import (
    build_single_keyword_tab,
    build_keyword_comparison_tab,
    build_category_analysis_tab,
    build_category_comparison_tab,
    build_selected_festival_tab
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
            build_selected_festival_tab()

    return demo