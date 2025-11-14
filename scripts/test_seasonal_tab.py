"""
계절별 탭 기능 간단 테스트
"""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

print("=== 계절별 탭 모듈 임포트 테스트 ===\n")

try:
    print("[1/4] seasonal_wordcloud 임포트 테스트...")
    from src.infrastructure.reporting import seasonal_wordcloud
    print("   [OK] seasonal_wordcloud 임포트 성공")

    print("\n[2/4] seasonal_analysis 임포트 테스트...")
    from src.application import seasonal_analysis
    print("   [OK] seasonal_analysis 임포트 성공")

    print("\n[3/4] seasonal_tab 임포트 테스트...")
    from src.presentation import seasonal_tab
    print("   [OK] seasonal_tab 임포트 성공")

    print("\n[4/4] 데이터 로드 테스트...")
    df = seasonal_analysis.load_seasonal_data()
    print(f"   [OK] 트렌드 데이터 로드 성공: {len(df)}개 축제")
    print(f"   계절별 분포: {df['season'].value_counts().to_dict()}")

    print("\n=== 모든 테스트 통과! ===")
    print("\n이제 앱을 실행할 수 있습니다:")
    print("  python app_llm.py")

except FileNotFoundError as e:
    print(f"\n   [ERROR] 데이터 파일 없음: {e}")
    print("   scripts/collect_sample_100.py를 먼저 실행해주세요.")

except Exception as e:
    print(f"\n   [ERROR] {e}")
    import traceback
    traceback.print_exc()
