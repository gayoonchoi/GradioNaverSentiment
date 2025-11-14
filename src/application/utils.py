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

def create_festinsight_table(results: dict, keyword: str) -> pd.DataFrame:
    """FestInsight_Analysis_Table 형식의 통합 데이터프레임을 생성합니다."""
    try:
        # DB에서 축제 상세 정보 가져오기
        from ..infrastructure.web.tour_api_client import get_festival_details
        festival_details = get_festival_details(keyword)

        # 기본 정보는 results에서 가져옴
        trend_metrics = results.get("trend_metrics", {})

        table_data = {
            'keyword': keyword,
            'addr1': festival_details.get('addr1', 'N/A') if festival_details else 'N/A',
            'addr2': festival_details.get('addr2', 'N/A') if festival_details else 'N/A',
            'areaCode': festival_details.get('areacode', 'N/A') if festival_details else 'N/A',
            'eventStartDate': results.get('festival_start_date').strftime('%Y%m%d') if results.get('festival_start_date') else 'N/A',
            'eventEndDate': results.get('festival_end_date').strftime('%Y%m%d') if results.get('festival_end_date') else 'N/A',
            'eventPeriod': results.get('event_period', 'N/A'),
            'trend_index': trend_metrics.get('trend_index', 0),
            'sentiment_score': round(results.get('total_sentiment_score', 50.0), 2),
            'positive_ratio': round((results.get('total_pos', 0) / results.get('total_sentiment_frequency', 1)) * 100, 2) if results.get('total_sentiment_frequency', 0) > 0 else 0,
            'negative_ratio': round((results.get('total_neg', 0) / results.get('total_sentiment_frequency', 1)) * 100, 2) if results.get('total_sentiment_frequency', 0) > 0 else 0,
            'complaint_factor': '주요 불만 사항 참조',  # 별도 요약 텍스트로 제공
            'satisfaction_delta': round(results.get('satisfaction_delta', 0), 2),
            'theme_sentiment_avg': 'N/A',  # 단일 키워드 분석에서는 해당 없음
            'emotion_keyword_freq': str(results.get('emotion_keyword_freq', {}))
        }

        return pd.DataFrame([table_data])
    except Exception as e:
        print(f"FestInsight 테이블 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def create_festinsight_table_for_category(results: dict, category_name: str) -> pd.DataFrame:
    """카테고리 분석 결과를 FestInsight_Analysis_Table 형식으로 변환합니다."""
    try:
        festival_results = results.get('individual_festival_results_df', pd.DataFrame())

        if festival_results.empty:
            return pd.DataFrame()

        # 기존 축제 요약 데이터프레임을 FestInsight 형식으로 변환
        table_data_list = []
        for _, row in festival_results.iterrows():
            table_data = {
                'keyword': row.get('축제명', 'N/A'),
                'addr1': 'N/A',
                'addr2': 'N/A',
                'areaCode': 'N/A',
                'eventStartDate': 'N/A',
                'eventEndDate': 'N/A',
                'eventPeriod': row.get('축제 기간 (일)', 'N/A'),
                'trend_index': row.get('트렌드 지수 (%)', 'N/A'),
                'sentiment_score': row.get('감성 점수', 'N/A'),
                'positive_ratio': row.get('긍정 비율 (%)', 'N/A'),
                'negative_ratio': row.get('부정 비율 (%)', 'N/A'),
                'complaint_factor': row.get('주요 불만 사항 요약', 'N/A')[:100] if pd.notna(row.get('주요 불만 사항 요약')) else 'N/A',
                'satisfaction_delta': row.get('만족도 변화', 'N/A'),
                'theme_sentiment_avg': results.get('theme_sentiment_avg', 'N/A'),
                'emotion_keyword_freq': row.get('주요 감성 키워드', 'N/A')
            }
            table_data_list.append(table_data)

        return pd.DataFrame(table_data_list)
    except Exception as e:
        print(f"카테고리 FestInsight 테이블 생성 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

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

def calculate_satisfaction_boundaries(scores: list) -> dict:
    """
    감성 점수 리스트로부터 IQR 기반 이상치를 제거하고,
    만족도 5단계 분류를 위한 경계값을 계산합니다.

    Returns:
        dict: {
            "boundaries": {mean, std, very_dissatisfied_upper, dissatisfied_upper, neutral_upper, satisfied_upper},
            "filtered_scores": 이상치 제거된 점수 리스트,
            "outliers": 이상치 리스트
        }
    """
    import numpy as np

    if not scores:
        return {
            "boundaries": {},
            "filtered_scores": [],
            "outliers": [],
        }

    q1 = np.percentile(scores, 25)
    q3 = np.percentile(scores, 75)
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr

    filtered_scores = [s for s in scores if lower_bound <= s <= upper_bound]
    outliers = [s for s in scores if s < lower_bound or s > upper_bound]

    if not filtered_scores:
        filtered_scores = scores

    mean = np.mean(filtered_scores)
    std = np.std(filtered_scores)

    # Handle case where all scores are identical
    if np.isclose(std, 0):
        std = 0.1

    boundaries = {
        "mean": mean,
        "std": std,
        "very_dissatisfied_upper": mean - 1.5 * std,
        "dissatisfied_upper": mean - 0.5 * std,
        "neutral_upper": mean + 0.5 * std,
        "satisfied_upper": mean + 1.5 * std,
    }
    return {
        "boundaries": boundaries,
        "filtered_scores": filtered_scores,
        "outliers": outliers,
    }

def map_score_to_level(score: float, boundaries: dict) -> int:
    """
    감성 점수를 5단계 만족도 레벨로 매핑합니다.

    Args:
        score: 감성 점수 (-2.0 ~ +2.0 범위)
        boundaries: calculate_satisfaction_boundaries()로 계산된 경계값 딕셔너리

    Returns:
        int: 1 (매우 불만족) ~ 5 (매우 만족)
    """
    if not boundaries:
        return 3  # Default to neutral if no boundaries
    if score < boundaries["very_dissatisfied_upper"]:
        return 1  # 매우 불만족
    elif score < boundaries["dissatisfied_upper"]:
        return 2  # 불만족
    elif score < boundaries["neutral_upper"]:
        return 3  # 보통
    elif score < boundaries["satisfied_upper"]:
        return 4  # 만족
    else:
        return 5  # 매우 만족

def generate_distribution_interpretation(satisfaction_counts: dict, total_count: int, boundaries: dict, avg_satisfaction: float) -> str:
    """
    LLM을 사용하여 만족도 분포에 대한 자연어 해석을 생성합니다.

    Args:
        satisfaction_counts: {'매우 불만족': N, '불만족': N, ...} 형태의 카운트 딕셔너리
        total_count: 전체 문장 수
        boundaries: 만족도 경계값 딕셔너리
        avg_satisfaction: 평균 만족도 (1.0 ~ 5.0)

    Returns:
        str: 마크다운 형식의 해석 텍스트
    """
    try:
        llm = get_llm_client(model="gemini-2.5-pro")

        # 카운트와 비율 계산
        labels = ["매우 불만족", "불만족", "보통", "만족", "매우 만족"]
        counts_str = "\n".join([f"- {label}: {satisfaction_counts.get(label, 0)}개 ({satisfaction_counts.get(label, 0) / total_count * 100:.1f}%)"
                                for label in labels])

        prompt = f"""다음은 축제 리뷰의 만족도 분포 데이터입니다:

**전체 리뷰 문장 수**: {total_count}개
**평균 만족도**: {avg_satisfaction:.2f} / 5.0

**만족도 분포**:
{counts_str}

**통계 정보**:
- 평균값: {boundaries.get('mean', 0):.2f}
- 표준편차: {boundaries.get('std', 0):.2f}

위 데이터를 바탕으로 **2-3문장**으로 만족도 분포를 해석해주세요.
- 어느 만족도 구간이 가장 많은지
- 전반적인 평가 경향은 어떠한지
- 특이사항이 있다면 무엇인지

간결하고 명확하게 작성해주세요."""

        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"만족도 분포 해석 생성 중 오류: {e}")
        traceback.print_exc()
        return f"평균 만족도는 {avg_satisfaction:.2f} / 5.0점입니다. 총 {total_count}개의 리뷰 문장이 분석되었습니다."