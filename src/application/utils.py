# src/application/utils.py
import pandas as pd
import re
import math
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from ..infrastructure.llm_client import get_llm_client # 상대 경로 임포트 수정

PAGE_SIZE = 10

def change_page(full_df, page_num):
    if not isinstance(full_df, pd.DataFrame) or full_df.empty:
        return pd.DataFrame(), 1, "/ 1"
    try:
        page_num = int(page_num)
        total_rows = len(full_df)
        total_pages = math.ceil(total_rows / PAGE_SIZE) if total_rows > 0 else 1
        page_num = max(1, min(page_num, total_pages))
        start_idx = (page_num - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        return full_df.iloc[start_idx:end_idx], page_num, f"/ {total_pages}"
    except Exception as e:
        print(f"페이지 변경 중 오류: {e}")
        traceback.print_exc()
        return pd.DataFrame(), 1, "/ 1"

def get_season(postdate: str) -> str:
    try:
        if not postdate or len(postdate) < 6: # 유효성 검사 추가
             return "정보없음"
        month = int(postdate[4:6])
        if month in [3, 4, 5]: return "봄"
        elif month in [6, 7, 8]: return "여름"
        elif month in [9, 10, 11]: return "가을"
        else: return "겨울"
    except:
        return "정보없음"

def save_df_to_csv(df: pd.DataFrame, base_name: str, keyword: str) -> str:
    if df is None or df.empty: return None
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 파일명으로 사용할 수 없는 문자 제거 강화
        sanitized_keyword = re.sub(r'[\\/*?"<>|:\s]+', '_', keyword) if keyword else "result"
        # 키워드가 너무 길 경우 잘라내기
        sanitized_keyword = sanitized_keyword[:50]
        csv_filepath = f"{sanitized_keyword}_{base_name}_{timestamp}.csv"
        df.to_csv(csv_filepath, index=False, encoding='utf-8-sig')
        return csv_filepath
    except Exception as e:
        print(f"CSV 저장 중 오류 ({keyword}): {e}")
        return None

def summarize_negative_feedback(sentences: list) -> str:
    if not sentences: return ""
    try:
        llm = get_llm_client(model="gemini-2.5-pro") # 모델명 확인
        unique_sentences = sorted(list(set(filter(None, sentences))), key=len, reverse=True) # None 값 제거
        if not unique_sentences: return "" # 빈 리스트 처리

        negative_feedback_str = "\n- ".join(unique_sentences[:50])
        prompt = f'''[수집된 부정적인 의견]\n- {negative_feedback_str}\n\n[요청] 위 의견들을 종합하여 주요 불만 사항을 1., 2., 3. ... 형식의 목록으로 요약해주세요. 만약 의견이 없다면 '특별한 불만 사항 없음'이라고 답해주세요.'''
        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"부정적 의견 요약 중 오류 발생: {e}")
        return "부정적 의견을 요약하는 데 실패했습니다."

def create_driver():
    """웹 드라이버 생성"""
    try:
        service = Service(ChromeDriverManager().install())
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        # 필요시 User-Agent 추가
        # chrome_options.add_argument("user-agent=...")
        return webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        print(f"WebDriver 생성 실패: {e}")
        traceback.print_exc()
        raise RuntimeError("WebDriver를 생성할 수 없습니다. Chrome 또는 ChromeDriver 설치를 확인하세요.") from e

def calculate_trend_metrics(trend_df: pd.DataFrame, start_date: datetime, end_date: datetime):
    """트렌드 데이터프레임과 축제 기간을 바탕으로 트렌드 관련 지표들을 계산합니다."""
    if trend_df.empty or not start_date or not end_date:
        return {
            "trend_index": 0,
            "after_trend_index": 0,
            "before_avg": 0,
            "during_avg": 0,
            "after_avg": 0,
        }

    try:
        # 날짜 타입을 pandas datetime으로 통일
        trend_df['period'] = pd.to_datetime(trend_df['period'])
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # 각 기간 정의
        before_period_start = start_date - pd.Timedelta(days=30)
        after_period_end = end_date + pd.Timedelta(days=30)

        # 기간별 데이터 필터링
        before_df = trend_df[(trend_df['period'] >= before_period_start) & (trend_df['period'] < start_date)]
        during_df = trend_df[(trend_df['period'] >= start_date) & (trend_df['period'] <= end_date)]
        after_df = trend_df[(trend_df['period'] > end_date) & (trend_df['period'] <= after_period_end)]

        # 각 기간별 평균 계산
        before_avg = before_df['ratio'].mean() if not before_df.empty else 0
        during_avg = during_df['ratio'].mean() if not during_df.empty else 0
        after_avg = after_df['ratio'].mean() if not after_df.empty else 0

        # 트렌드 지수 계산
        # 축제 전 대비 축제 중 트렌드 변화 (0으로 나누는 경우 방지)
        trend_index = (during_avg / before_avg) * 100 if before_avg > 0 else (during_avg * 100 if during_avg > 0 else 0)
        # 축제 중 대비 축제 후 트렌드 변화
        after_trend_index = (after_avg / during_avg) * 100 if during_avg > 0 else (after_avg * 100 if after_avg > 0 else 0)
        
        return {
            "trend_index": round(trend_index, 1),
            "after_trend_index": round(after_trend_index, 1),
            "before_avg": round(before_avg, 1),
            "during_avg": round(during_avg, 1),
            "after_avg": round(after_avg, 1),
        }
    except Exception as e:
        print(f"트렌드 지표 계산 중 오류: {e}")
        traceback.print_exc()
        return {
            "trend_index": 0, "after_trend_index": 0, "before_avg": 0, "during_avg": 0, "after_avg": 0,
        }