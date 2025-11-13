

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

