# -*- coding: utf-8 -*-

# 1. 환경 설정 초기화 (가장 먼저 실행되어야 합니다)
import src.config

# 2. 필요한 UI 및 애플리케이션 모듈 임포트
from src.presentation.gradio_ui import create_ui

# 3. 메인 실행 블록
if __name__ == "__main__":
    print("Gradio 앱을 시작합니다. 브라우저에서 UI를 확인하세요.")
    print(
        "이제 Selenium과 webdriver-manager가 필요합니다. 'pip install -r requirements.txt'를 실행해주세요."
    )
    print(
        "네이버 API 키(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)와 Google API 키(GOOGLE_API_KEY)가 .env 파일에 설정되어 있어야 합니다."
    )
    
    # UI 생성 및 실행
    demo = create_ui()
    demo.launch()