"""
축제별 네이버 트렌드 데이터 수집 스크립트

이 스크립트는 database/축제공연행사csv.CSV의 모든 축제에 대해
네이버 트렌드 API를 호출하여 검색량 데이터를 수집하고
festival_trends_summary.csv로 저장합니다.

실행 방법:
    python scripts/collect_all_trends.py

주의: 네이버 API 쿼터 제한이 있으므로 시간이 오래 걸립니다 (약 1-2시간)
"""

import os
import sys
import pandas as pd
import datetime
import time
import random
from tqdm import tqdm

# 프로젝트 루트를 Python path에 추가
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.infrastructure.web.naver_trend_api import get_trend_data
from src.config import get_naver_trend_api_keys

# 파일 경로
CSV_PATH = os.path.join(PROJECT_ROOT, "database", "축제공연행사csv.CSV")
OUTPUT_PATH = os.path.join(PROJECT_ROOT, "database", "festival_trends_summary.csv")

def classify_season(month: int) -> str:
    """월 정보를 기반으로 계절 분류"""
    if month in [3, 4, 5]:
        return "봄"
    elif month in [6, 7, 8]:
        return "여름"
    elif month in [9, 10, 11]:
        return "가을"
    else:  # 12, 1, 2
        return "겨울"

def collect_trend_for_festival(festival_name: str, start_date_str: str, end_date_str: str):
    """
    단일 축제의 트렌드 데이터를 수집하고 요약 통계를 반환

    Args:
        festival_name: 축제명
        start_date_str: 행사 시작일 (YYYYMMDD)
        end_date_str: 행사 종료일 (YYYYMMDD)

    Returns:
        dict: 요약 통계 (max_ratio, mean_ratio, max_date 등)
              실패 시 None
    """
    try:
        # 날짜 변환
        start_date = datetime.datetime.strptime(str(int(start_date_str)), "%Y%m%d")
        end_date = datetime.datetime.strptime(str(int(end_date_str)), "%Y%m%d")

        # 오늘 날짜 이후의 축제는 스킵
        today = datetime.date.today()
        if start_date.date() > today:
            return None

        # API 호출 기간: 축제 시작 30일 전 ~ 종료 30일 후
        api_start = start_date - datetime.timedelta(days=30)
        api_end = min(end_date + datetime.timedelta(days=30), datetime.datetime.now())

        # 네이버 트렌드 API 호출
        df_trend = get_trend_data(festival_name, api_start.date(), api_end.date())

        if df_trend.empty:
            return None

        # 통계 계산
        max_ratio = float(df_trend['ratio'].max())
        mean_ratio = float(df_trend['ratio'].mean())
        max_date = df_trend.loc[df_trend['ratio'].idxmax(), 'period']

        return {
            'festival_name': festival_name,
            'event_start_date': start_date.strftime("%Y-%m-%d"),
            'event_end_date': end_date.strftime("%Y-%m-%d"),
            'season': classify_season(start_date.month),
            'max_ratio': round(max_ratio, 2),
            'mean_ratio': round(mean_ratio, 2),
            'max_date': max_date.strftime("%Y-%m-%d"),
            'data_points': len(df_trend)
        }

    except Exception as e:
        print(f"❌ {festival_name} 처리 중 오류: {e}")
        return None

def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🎪 축제별 네이버 트렌드 데이터 수집 시작")
    print("=" * 60)

    # API 키 확인
    try:
        client_id, client_secret = get_naver_trend_api_keys()
        print(f"✅ 네이버 API 키 확인 완료")
    except Exception as e:
        print(f"❌ 네이버 API 키 설정 오류: {e}")
        print("config.py 또는 환경변수에서 API 키를 설정해주세요.")
        return

    # CSV 파일 로드
    print(f"\n📂 축제 데이터 로드 중: {CSV_PATH}")
    try:
        df_festivals = pd.read_csv(CSV_PATH, encoding='cp949')
        print(f"✅ 총 {len(df_festivals)}개 축제 로드 완료")
    except Exception as e:
        print(f"❌ CSV 파일 로드 실패: {e}")
        return

    # 필요한 컬럼만 추출
    df_festivals = df_festivals[['title', 'eventstartdate', 'eventenddate']].copy()
    df_festivals = df_festivals.dropna(subset=['eventstartdate', 'eventenddate'])

    print(f"✅ 유효한 축제 {len(df_festivals)}개 필터링 완료")

    # 기존 데이터 확인 (이어서 수집)
    if os.path.exists(OUTPUT_PATH):
        existing_df = pd.read_csv(OUTPUT_PATH)
        existing_festivals = set(existing_df['festival_name'].tolist())
        print(f"\n📊 기존 수집 데이터 발견: {len(existing_festivals)}개")

        # 아직 수집하지 않은 축제만 필터링
        df_festivals = df_festivals[~df_festivals['title'].isin(existing_festivals)]
        print(f"✅ 남은 수집 대상: {len(df_festivals)}개")

        if len(df_festivals) == 0:
            print("✅ 모든 축제 데이터가 이미 수집되었습니다!")
            return
    else:
        existing_df = None

    # 트렌드 데이터 수집
    results = []
    failed_count = 0

    print(f"\n🚀 트렌드 데이터 수집 시작...")
    print(f"⏱️  예상 소요 시간: 약 {len(df_festivals) * 1.5 / 60:.1f}분")
    print("=" * 60)

    for idx, row in tqdm(df_festivals.iterrows(), total=len(df_festivals), desc="수집 진행"):
        festival_name = row['title']
        start_date = row['eventstartdate']
        end_date = row['eventenddate']

        # 트렌드 데이터 수집
        result = collect_trend_for_festival(festival_name, start_date, end_date)

        if result:
            results.append(result)

            # 진행 상황 출력 (10개마다)
            if len(results) % 10 == 0:
                tqdm.write(f"✅ 진행: {len(results)}개 수집 완료, {failed_count}개 실패")
        else:
            failed_count += 1

        # API Rate Limiting (1.2초 대기)
        time.sleep(1.2 + random.uniform(0, 0.3))

        # 중간 저장 (100개마다)
        if len(results) % 100 == 0 and len(results) > 0:
            temp_df = pd.DataFrame(results)
            if existing_df is not None:
                temp_df = pd.concat([existing_df, temp_df], ignore_index=True)
            temp_df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')
            tqdm.write(f"💾 중간 저장 완료: {len(temp_df)}개")

    print("\n" + "=" * 60)
    print(f"✅ 수집 완료!")
    print(f"   - 성공: {len(results)}개")
    print(f"   - 실패: {failed_count}개")
    print("=" * 60)

    # 최종 데이터프레임 생성
    if len(results) > 0:
        new_df = pd.DataFrame(results)

        # 기존 데이터와 병합
        if existing_df is not None:
            final_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            final_df = new_df

        # 중복 제거 및 정렬
        final_df = final_df.drop_duplicates(subset=['festival_name'], keep='last')
        final_df = final_df.sort_values('max_ratio', ascending=False).reset_index(drop=True)

        # CSV 저장
        final_df.to_csv(OUTPUT_PATH, index=False, encoding='utf-8-sig')

        print(f"\n📂 저장 완료: {OUTPUT_PATH}")
        print(f"   - 총 축제 수: {len(final_df)}개")
        print(f"   - 계절별 분포:")
        print(final_df['season'].value_counts().to_string())

        print("\n📊 상위 10개 인기 축제:")
        print(final_df[['festival_name', 'season', 'max_ratio']].head(10).to_string(index=False))

    else:
        print("⚠️ 수집된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
