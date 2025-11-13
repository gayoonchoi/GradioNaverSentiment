

import os
import re
import requests
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import io
import uuid
from ...config import get_naver_trend_api_keys

def safe_filename(name: str) -> str:
    """Windows 금지문자들을 유니코드 대체 문자로 변환"""
    invalid_pattern = r'[\\/:*?"<>|]'
    replace_map = {
        '\\': '＼',
        '/': '／',
        ':': '꞉',
        '*': '＊',
        '?': '？',
        '"': '＂',
        '<': '‹',
        '>': '›',
        '|': '｜'
    }
    return re.sub(invalid_pattern, lambda m: replace_map[m.group()], name)

def get_trend_data(keyword, start_date, end_date):
    """네이버 데이터랩 트렌드 API를 호출하여 데이터를 반환합니다."""
    client_id, client_secret = get_naver_trend_api_keys()
    url = "https://openapi.naver.com/v1/datalab/search"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "Content-Type": "application/json"
    }
    body = {
        "startDate": start_date.strftime("%Y-%m-%d"),
        "endDate": end_date.strftime("%Y-%m-%d"),
        "timeUnit": "date",
        "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}]
    }
    res = requests.post(url, headers=headers, json=body)

    if res.status_code != 200:
        print(f"❌ {keyword} 오류: {res.status_code}")
        return pd.DataFrame()

    results = res.json().get('results', [])
    if not results or not results[0].get('data'):
        print(f"⚠️ {keyword} 검색 결과 없음")
        return pd.DataFrame()

    df = pd.DataFrame(results[0]['data'])
    df['period'] = pd.to_datetime(df['period'])
    df['ratio'] = df['ratio'].astype(float)
    df['keyword'] = keyword
    return df

def create_trend_graph(keyword: str, festival_start_date=None, festival_end_date=None):
    """특정 키워드에 대한 트렌드 그래프를 생성하여 이미지 파일 경로와 데이터프레임을 반환합니다."""
    today = datetime.date.today()
    start_for_api = today - datetime.timedelta(days=365)
    end_for_api = today

    df_trend = get_trend_data(keyword, start_for_api, end_for_api)

    if df_trend.empty:
        return None, pd.DataFrame()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df_trend['period'], df_trend['ratio'], marker='o', linestyle='-', label=keyword)

    if festival_start_date and festival_end_date:
        ax.axvline(pd.to_datetime(festival_start_date), color='green', linestyle='--', label='행사 시작')
        ax.axvline(pd.to_datetime(festival_end_date), color='red', linestyle='--', label='행사 종료')

    ax.set_title(f"'{keyword}' 지난 1년간 검색어 트렌드")
    ax.set_xlabel("날짜")
    ax.set_ylabel("검색량 지수")
    ax.legend()
    ax.grid(True)
    fig.tight_layout()

    # 임시 파일로 저장
    temp_dir = os.path.join(os.getcwd(), "temp_images")
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"{uuid.uuid4()}.png")

    fig.savefig(file_path)
    plt.close(fig)

    return file_path, df_trend

def create_focused_trend_graph(keyword: str, festival_start_date, festival_end_date):
    """축제 시작일 기준 ±1개월 기간의 트렌드 그래프를 생성합니다.
    축제 기간이 없으면 최근 60일간의 트렌드를 보여줍니다."""

    try:
        # 축제 기간이 없으면 최근 60일간의 데이터로 대체
        if not festival_start_date or not festival_end_date:
            print(f"⚠️ '{keyword}' 축제 기간 정보 없음 - 최근 60일 트렌드로 대체")
            today = datetime.date.today()
            start_for_api = today - datetime.timedelta(days=60)
            end_for_api = today
            has_festival_dates = False
        else:
            # datetime 객체로 변환 (문자열일 수도 있고 datetime일 수도 있음)
            if isinstance(festival_start_date, str):
                festival_start_date = datetime.datetime.strptime(festival_start_date, "%Y%m%d")
            if isinstance(festival_end_date, str):
                festival_end_date = datetime.datetime.strptime(festival_end_date, "%Y%m%d")

            # 축제 시작일 기준 ±1개월 범위 설정
            start_for_api = festival_start_date - datetime.timedelta(days=30)
            end_for_api = festival_end_date + datetime.timedelta(days=30)
            has_festival_dates = True

        # 오늘 날짜를 넘지 않도록 제한
        today = datetime.date.today()
        # end_for_api가 date인지 datetime인지 확인
        if isinstance(end_for_api, datetime.datetime):
            end_for_api_date = end_for_api.date()
        else:
            end_for_api_date = end_for_api

        if end_for_api_date > today:
            end_for_api = today

        df_trend = get_trend_data(keyword, start_for_api, end_for_api)

        if df_trend.empty:
            print(f"❌ '{keyword}' 트렌드 데이터를 가져올 수 없음")
            return None, pd.DataFrame()

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(df_trend['period'], df_trend['ratio'], marker='o', linestyle='-', linewidth=2, label=keyword, color='#1f77b4')

        if has_festival_dates:
            # 축제 시작/종료일 표시
            ax.axvline(pd.to_datetime(festival_start_date), color='green', linestyle='--', linewidth=2, label='행사 시작')
            ax.axvline(pd.to_datetime(festival_end_date), color='red', linestyle='--', linewidth=2, label='행사 종료')

            # 축제 기간 배경 강조
            ax.axvspan(pd.to_datetime(festival_start_date), pd.to_datetime(festival_end_date),
                       alpha=0.2, color='yellow', label='행사 기간')

            title = f"'{keyword}' 축제 기간 집중 트렌드 (시작일 ±1개월)"
        else:
            title = f"'{keyword}' 최근 60일 검색량 트렌드"

        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel("날짜", fontsize=12)
        ax.set_ylabel("검색량 지수", fontsize=12)
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()

        # 임시 파일로 저장
        temp_dir = os.path.join(os.getcwd(), "temp_images")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_focused.png")

        fig.savefig(file_path, dpi=100)
        plt.close(fig)

        print(f"✅ '{keyword}' 집중 트렌드 그래프 생성 완료: {file_path}")

        return file_path, df_trend

    except Exception as e:
        print(f"❌ 집중 트렌드 그래프 생성 중 오류 ({keyword}): {e}")
        import traceback
        traceback.print_exc()
        return None, pd.DataFrame()

