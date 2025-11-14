"""
트렌드 수집 스크립트 테스트 (상위 10개만)
"""

import os
import sys
import pandas as pd
import datetime

# 프로젝트 루트를 Python path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.infrastructure.web.naver_trend_api import get_trend_data

# 테스트: 상위 10개 축제만
CSV_PATH = os.path.join(PROJECT_ROOT, "database", "축제공연행사csv.CSV")

def classify_season(month: int) -> str:
    """월 정보를 기반으로 계절 분류"""
    if month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    elif month in [9, 10, 11]:
        return "가을"
    else:
        return "겨울"

print("=== 트렌드 수집 테스트 (상위 10개) ===")
print("=" * 60)

# CSV 로드
df = pd.read_csv(CSV_PATH, encoding='cp949')
df = df[['title', 'eventstartdate', 'eventenddate']].dropna()

results = []
today = datetime.date.today()

for idx, row in df.head(10).iterrows():
    festival_name = row['title']
    start_date_str = str(int(row['eventstartdate']))
    end_date_str = str(int(row['eventenddate']))

    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y%m%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y%m%d")

        # 미래 축제는 스킵
        if start_date.date() > today:
            print(f"[SKIP] {festival_name}: 미래 축제")
            continue

        # API 호출
        api_start = start_date - datetime.timedelta(days=30)
        api_end = min(end_date + datetime.timedelta(days=30), datetime.datetime.now())

        print(f"[COLLECT] {festival_name} 수집 중...")
        df_trend = get_trend_data(festival_name, api_start.date(), api_end.date())

        if not df_trend.empty:
            max_ratio = float(df_trend['ratio'].max())
            mean_ratio = float(df_trend['ratio'].mean())
            season = classify_season(start_date.month)

            results.append({
                'festival_name': festival_name,
                'season': season,
                'max_ratio': round(max_ratio, 2),
                'mean_ratio': round(mean_ratio, 2),
                'event_start': start_date.strftime("%Y-%m-%d")
            })
            print(f"   [OK] 성공: 최대 검색량={max_ratio}, 계절={season}")
        else:
            print(f"   [WARN] 데이터 없음")

    except Exception as e:
        print(f"   [ERROR] 오류: {e}")

print("\n" + "=" * 60)
print(f"[DONE] 테스트 완료: {len(results)}개 수집")

if results:
    test_df = pd.DataFrame(results)
    print("\n[RESULT] 수집 결과:")
    print(test_df.to_string(index=False))
