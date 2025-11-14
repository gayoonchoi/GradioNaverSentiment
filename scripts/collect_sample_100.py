"""
샘플 데이터 수집 (상위 100개 축제)
빠른 프로토타입 테스트용
"""

import os
import sys
import pandas as pd
import datetime
import time
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.infrastructure.web.naver_trend_api import get_trend_data

CSV_PATH = os.path.join(PROJECT_ROOT, "database", "축제공연행사csv.CSV")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "database", "festival_trends_summary.csv")

def classify_season(month: int) -> str:
    if month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    elif month in [9, 10, 11]:
        return "가을"
    else:
        return "겨울"

print("=== 샘플 데이터 수집 (상위 100개) ===")
print("=" * 60)

df = pd.read_csv(CSV_PATH, encoding='cp949')
df = df[['title', 'eventstartdate', 'eventenddate']].dropna()

results = []
today = datetime.date.today()
count = 0

for idx, row in df.iterrows():
    if count >= 100:
        break

    festival_name = row['title']
    start_date_str = str(int(row['eventstartdate']))
    end_date_str = str(int(row['eventenddate']))

    try:
        start_date = datetime.datetime.strptime(start_date_str, "%Y%m%d")
        end_date = datetime.datetime.strptime(end_date_str, "%Y%m%d")

        if start_date.date() > today:
            continue

        api_start = start_date - datetime.timedelta(days=30)
        api_end = min(end_date + datetime.timedelta(days=30), datetime.datetime.now())

        print(f"[{count+1}/100] {festival_name} 수집 중...")
        df_trend = get_trend_data(festival_name, api_start.date(), api_end.date())

        if not df_trend.empty:
            max_ratio = float(df_trend['ratio'].max())
            mean_ratio = float(df_trend['ratio'].mean())
            max_date = df_trend.loc[df_trend['ratio'].idxmax(), 'period']
            season = classify_season(start_date.month)

            results.append({
                'festival_name': festival_name,
                'event_start_date': start_date.strftime("%Y-%m-%d"),
                'event_end_date': end_date.strftime("%Y-%m-%d"),
                'season': season,
                'max_ratio': round(max_ratio, 2),
                'mean_ratio': round(mean_ratio, 2),
                'max_date': max_date.strftime("%Y-%m-%d"),
                'data_points': len(df_trend)
            })
            count += 1
            print(f"   [OK] 최대={max_ratio}, 평균={mean_ratio}, 계절={season}")

        time.sleep(1.2 + random.uniform(0, 0.3))

    except Exception as e:
        print(f"   [ERROR] {e}")

print("\n" + "=" * 60)
print(f"[DONE] 수집 완료: {len(results)}개")

if results:
    result_df = pd.DataFrame(results)
    result_df = result_df.sort_values('max_ratio', ascending=False).reset_index(drop=True)
    result_df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
    print(f"\n저장 완료: {OUTPUT_PATH}")
    print(f"\n계절별 분포:")
    print(result_df['season'].value_counts())
    print(f"\n상위 10개:")
    print(result_df[['festival_name', 'season', 'max_ratio']].head(10).to_string(index=False))
