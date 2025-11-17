# src/application/utils.py
import os
import pandas as pd
import re
import math
import json
import hashlib
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import traceback
from ..infrastructure.llm_client import get_llm_client # 상대 경로 임포트 수정

PAGE_SIZE = 10

# 캐시 설정
CACHE_DIR = "cache"
CACHE_EXPIRY_DAYS = 30  # 캐시 만료 기간 (일)

def get_cache_key(keyword: str, num_reviews: int) -> str:
    """키워드와 리뷰 개수로 캐시 키 생성"""
    key_str = f"{keyword}_{num_reviews}"
    return hashlib.md5(key_str.encode('utf-8')).hexdigest()

def get_cache_path(cache_key: str) -> str:
    """캐시 파일 경로 반환"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def is_cache_valid(cache_path: str) -> bool:
    """캐시 파일이 유효한지 확인 (존재 여부 및 만료 기간)"""
    if not os.path.exists(cache_path):
        return False

    # 캐시 파일 수정 시간 확인
    file_mtime = datetime.fromtimestamp(os.path.getmtime(cache_path))
    expiry_date = datetime.now() - timedelta(days=CACHE_EXPIRY_DAYS)

    return file_mtime > expiry_date

def load_cached_analysis(keyword: str, num_reviews: int) -> dict:
    """캐시된 분석 결과 로드"""
    try:
        cache_key = get_cache_key(keyword, num_reviews)
        cache_path = get_cache_path(cache_key)

        if not is_cache_valid(cache_path):
            return None

        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)
            print(f"✅ 캐시된 분석 결과 사용: {keyword} (num_reviews={num_reviews})")
            return cached_data
    except Exception as e:
        print(f"⚠️ 캐시 로드 실패: {e}")
        return None

def save_analysis_to_cache(keyword: str, num_reviews: int, results: dict) -> None:
    """분석 결과를 캐시에 저장 (API 형식용)"""
    try:
        cache_key = get_cache_key(keyword, num_reviews)
        cache_path = get_cache_path(cache_key)

        # pandas DataFrame을 dict로 변환할 수 있도록 처리
        cacheable_results = {}
        for key, value in results.items():
            if isinstance(value, pd.DataFrame):
                cacheable_results[key] = value.to_dict('records')
            elif isinstance(value, (datetime,)):
                cacheable_results[key] = value.isoformat() if value else None
            elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
                cacheable_results[key] = value
            else:
                # 직렬화할 수 없는 타입은 문자열로 변환
                cacheable_results[key] = str(value)

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cacheable_results, f, ensure_ascii=False, indent=2)
            print(f"💾 분석 결과 캐시 저장: {keyword} (num_reviews={num_reviews})")
    except Exception as e:
        print(f"⚠️ 캐시 저장 실패 (분석은 계속 진행됨): {e}")

def save_raw_analysis_to_cache(keyword: str, num_reviews: int, results: dict) -> None:
    """원본 분석 결과를 캐시에 저장 (내부 재사용용)"""
    try:
        cache_key = get_cache_key(keyword, num_reviews) + "_raw"
        cache_path = get_cache_path(cache_key)

        # pandas DataFrame과 datetime을 JSON 직렬화 가능하도록 변환
        cacheable_results = {}
        for key, value in results.items():
            if isinstance(value, pd.DataFrame):
                # DataFrame을 records 형식과 함께 columns 정보도 저장
                cacheable_results[key] = {
                    '_type': 'DataFrame',
                    'data': value.to_dict('records'),
                    'columns': list(value.columns)
                }
            elif isinstance(value, (datetime,)):
                cacheable_results[key] = {
                    '_type': 'datetime',
                    'value': value.isoformat() if value else None
                }
            elif isinstance(value, (dict, list, str, int, float, bool, type(None))):
                cacheable_results[key] = value
            else:
                # 직렬화할 수 없는 타입은 문자열로 변환
                cacheable_results[key] = str(value)

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cacheable_results, f, ensure_ascii=False, indent=2)
            print(f"💾 원본 분석 결과 캐시 저장: {keyword} (num_reviews={num_reviews})")
    except Exception as e:
        print(f"⚠️ 원본 캐시 저장 실패 (분석은 계속 진행됨): {e}")

def load_raw_cached_analysis(keyword: str, num_reviews: int) -> dict:
    """캐시된 원본 분석 결과 로드"""
    try:
        cache_key = get_cache_key(keyword, num_reviews) + "_raw"
        cache_path = get_cache_path(cache_key)

        if not is_cache_valid(cache_path):
            return None

        with open(cache_path, 'r', encoding='utf-8') as f:
            cached_data = json.load(f)

            # DataFrame과 datetime 복원
            restored_results = {}
            for key, value in cached_data.items():
                if isinstance(value, dict) and value.get('_type') == 'DataFrame':
                    # DataFrame 복원
                    restored_results[key] = pd.DataFrame(value['data'], columns=value['columns'])
                elif isinstance(value, dict) and value.get('_type') == 'datetime':
                    # datetime 복원
                    restored_results[key] = datetime.fromisoformat(value['value']) if value['value'] else None
                else:
                    restored_results[key] = value

            print(f"✅ 캐시된 원본 분석 결과 사용: {keyword} (num_reviews={num_reviews})")
            return restored_results
    except Exception as e:
        print(f"⚠️ 원본 캐시 로드 실패: {e}")
        traceback.print_exc()
        return None

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
        # 숫자만 추출하여 YYYYMMDD 형식으로 만듭니다.
        cleaned_date = re.sub(r'\D', '', postdate)
        if not cleaned_date or len(cleaned_date) < 6:
            return "정보없음"
        
        month = int(cleaned_date[4:6])
        if month in [3, 4, 5]: return "봄"
        elif month in [6, 7, 8]: return "여름"
        elif month in [9, 10, 11]: return "가을"
        else: return "겨울"
    except (ValueError, IndexError):
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
    if not sentences:
        if os.environ.get("LOG_DEBUG") == "true":
            print("[DEBUG] summarize_negative_feedback: No sentences provided, returning empty string.")
        return ""
    try:
        llm = get_llm_client(model="gemini-2.5-pro")

        if os.environ.get("LOG_DEBUG") == "true":
            print(f"[DEBUG] summarize_negative_feedback: Received {len(sentences)} sentences.")
            print(f"[DEBUG] First 3 sentences: {sentences[:3]}")

        # 빈 문장, None, 너무 짧은 문장(3자 미만) 필터링
        filtered_sentences = [s for s in sentences if s and isinstance(s, str) and len(s.strip()) >= 3]

        if os.environ.get("LOG_DEBUG") == "true":
            print(f"[DEBUG] After basic filtering: {len(filtered_sentences)} sentences")

        unique_sentences = sorted(list(set(filtered_sentences)), key=len, reverse=True)

        if not unique_sentences:
            if os.environ.get("LOG_DEBUG") == "true":
                print("[DEBUG] summarize_negative_feedback: No unique sentences after filtering, returning empty string.")
            # 부정 판정은 있지만 문장이 없는 경우를 위한 명시적 메시지
            return ""

        negative_feedback_str = "\n- ".join(unique_sentences[:50])
        
        if os.environ.get("LOG_DEBUG") == "true":
            print(f"[DEBUG] summarize_negative_feedback: negative_feedback_str length: {len(negative_feedback_str)}")
            print(f"[DEBUG] negative_feedback_str (first 200 chars): {negative_feedback_str[:200]}")

        prompt = f'''[수집된 부정적인 의견]\n- {negative_feedback_str}\n\n[요청] 위 의견들을 종합하여 주요 불만 사항을 1., 2., 3. ... 형식의 목록으로 요약해주세요. 만약 의견이 없다면 '특별한 불만 사항 없음'이라고 답해주세요.'''
        
        if os.environ.get("LOG_DEBUG") == "true":
            print(f"[DEBUG] summarize_negative_feedback: LLM Prompt (first 500 chars): {prompt[:500]}")

        response = llm.invoke(prompt)
        
        if os.environ.get("LOG_DEBUG") == "true":
            print(f"[DEBUG] summarize_negative_feedback: LLM Response: {response.content.strip()}")

        return response.content.strip()
    except Exception as e:
        print(f"부정적 의견 요약 중 오류 발생: {e}")
        traceback.print_exc()
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

def generate_distribution_interpretation(satisfaction_counts: dict, total_count: int, boundaries: dict, avg_satisfaction: float,
                                        all_scores: list = None, outliers: list = None, total_pos: int = 0, total_neg: int = 0,
                                        trend_metrics: dict = None) -> str:
    """
    LLM을 사용하여 전체 차트 데이터(6개)를 종합 분석하여 자연어 해석을 생성합니다.

    Args:
        satisfaction_counts: {'매우 불만족': N, '불만족': N, ...} 형태의 카운트 딕셔너리
        total_count: 전체 문장 수
        boundaries: 만족도 경계값 딕셔너리
        avg_satisfaction: 평균 만족도 (1.0 ~ 5.0)
        all_scores: 절대 점수 리스트 (옵션)
        outliers: 이상치 리스트 (옵션)
        total_pos: 긍정 문장 수 (옵션)
        total_neg: 부정 문장 수 (옵션)
        trend_metrics: 트렌드 지표 (옵션)

    Returns:
        str: 마크다운 형식의 종합 해석 텍스트
    """
    try:
        llm = get_llm_client(model="gemini-2.5-pro")

        # 카운트와 비율 계산
        labels = ["매우 불만족", "불만족", "보통", "만족", "매우 만족"]
        counts_str = "\n".join([f"- {label}: {satisfaction_counts.get(label, 0)}개 ({satisfaction_counts.get(label, 0) / total_count * 100:.1f}%)"
                                for label in labels])

        # 1. 전체 긍정/부정 비율 데이터
        total_sentiment = total_pos + total_neg if (total_pos or total_neg) else total_count
        pos_ratio = (total_pos / total_sentiment * 100) if total_sentiment > 0 else 0
        neg_ratio = (total_neg / total_sentiment * 100) if total_sentiment > 0 else 0

        sentiment_ratio_str = f"""
### 1. 전체 긍정/부정 비율
- 긍정 문장: {total_pos}개 ({pos_ratio:.1f}%)
- 부정 문장: {total_neg}개 ({neg_ratio:.1f}%)"""

        # 2. 만족도 5단계 분포 데이터
        satisfaction_dist_str = f"""
### 2. 만족도 5단계 분포
{counts_str}
- 평균 만족도: {avg_satisfaction:.2f} / 5.0"""

        # 3. 절대 점수 분포 데이터
        score_dist_str = ""
        if all_scores:
            import numpy as np
            min_score = np.min(all_scores)
            max_score = np.max(all_scores)
            median_score = np.median(all_scores)
            score_dist_str = f"""
### 3. 절대 점수 분포
- 최소 점수: {min_score:.2f}
- 최대 점수: {max_score:.2f}
- 중간값: {median_score:.2f}
- 평균: {boundaries.get('mean', 0):.2f}
- 표준편차: {boundaries.get('std', 0):.2f}"""

        # 4. 이상치 분석 데이터
        outlier_str = ""
        if outliers is not None:
            outlier_ratio = (len(outliers) / total_count * 100) if total_count > 0 else 0
            outlier_str = f"""
### 4. 이상치 분석
- 이상치 개수: {len(outliers)}개 (전체의 {outlier_ratio:.1f}%)
- 해석: {'극단적인 의견이 다수 존재합니다.' if outlier_ratio > 10 else '대부분의 의견이 평균적인 범위 내에 있습니다.'}"""

        # 5. 트렌드 분석 데이터
        trend_str = ""
        if trend_metrics:
            trend_index = trend_metrics.get('trend_index', 0)
            before_avg = trend_metrics.get('before_avg', 0)
            during_avg = trend_metrics.get('during_avg', 0)
            after_avg = trend_metrics.get('after_avg', 0)
            trend_str = f"""
### 5&6. 트렌드 분석 (집중 & 전체)
- 축제 전 평균 검색량: {before_avg:.1f}
- 축제 중 평균 검색량: {during_avg:.1f}
- 축제 후 평균 검색량: {after_avg:.1f}
- 트렌드 지수: {trend_index:.1f}% (100 이상이면 축제 기간 동안 관심도 증가)"""

        prompt = f"""다음은 축제 리뷰의 종합 분석 데이터입니다. **6개의 차트 데이터를 모두 고려하여** 전문가 입장에서 종합적인 해석을 제공해주세요.

**전체 리뷰 문장 수**: {total_count}개
{sentiment_ratio_str}
{satisfaction_dist_str}
{score_dist_str}
{outlier_str}
{trend_str}

위의 **6가지 차트 데이터(긍정/부정 비율, 만족도 5단계, 절대 점수 분포, 이상치 분석, 트렌드 분석)를 모두 종합하여** 다음을 포함하는 **3-5문장**의 종합 해석을 작성해주세요:

1. 전반적인 평가 경향 (긍정 vs 부정)
2. 만족도 분포의 특징 (어느 구간에 집중되어 있는지)
3. 감성 점수의 분포 특성 (극단적 vs 중립적)
4. 이상치 존재 여부와 의미
5. 트렌드 지수를 고려한 화제성 vs 만족도 관계
6. 종합적인 축제 평가 및 시사점

간결하고 실용적인 인사이트를 제공해주세요."""

        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"종합 차트 해석 생성 중 오류: {e}")
        traceback.print_exc()
        return f"평균 만족도는 {avg_satisfaction:.2f} / 5.0점입니다. 긍정 비율은 {(total_pos/(total_pos+total_neg)*100) if (total_pos+total_neg) > 0 else 0:.1f}%입니다."

def generate_overall_summary(results: dict) -> str:
    """
    LLM을 사용하여 전체 분석 결과에 대한 종합 평가를 생성합니다.
    """
    try:
        llm = get_llm_client(model="gemini-2.5-pro")
        
        # 프롬프트에 사용할 주요 지표 추출
        keyword = results.get('keyword', '해당 축제')
        avg_satisfaction = results.get('avg_satisfaction', 3.0)
        total_pos = results.get('total_pos', 0)
        total_neg = results.get('total_neg', 0)
        pos_ratio = (total_pos / (total_pos + total_neg) * 100) if (total_pos + total_neg) > 0 else 0
        trend_index = results.get('trend_metrics', {}).get('trend_index', 0)
        distribution_interpretation = results.get('distribution_interpretation', '데이터 없음')
        negative_summary = results.get('negative_summary', '데이터 없음')

        prompt = f"""
        **{keyword}**에 대한 종합 분석 결과입니다. 아래 데이터를 바탕으로 전문가 입장에서 최종 평가를 내려주세요.

        ### 주요 지표
        - **평균 만족도**: {avg_satisfaction:.2f} / 5.0
        - **긍정/부정 비율**: 긍정 {pos_ratio:.1f}% / 부정 {100-pos_ratio:.1f}%
        - **화제성 (트렌드 지수)**: {trend_index:.1f} (100 이상이면 평균 이상)
        
        ### AI 분석 요약
        - **만족도 분포 해석**: {distribution_interpretation}
        - **주요 불만 사항**: {negative_summary}

        ### 최종 평가 요청
        위 모든 정보를 종합하여, 다음 항목을 포함하는 최종 평가를 마크다운 형식으로 작성해주세요.
        1.  **한줄 요약**: 이 축제의 핵심적인 평가를 한 문장으로 요약합니다. (예: "화제성은 높지만, 주차 문제 등 운영 개선이 필요한 축제입니다.")
        2.  **종합 의견**: 전반적인 긍정/부정 여론, 만족도 수준, 화제성을 종합적으로 고려한 상세 의견을 2-3문장으로 작성합니다.
        3.  **강점 (Pros)**: 분석 결과에서 나타난 긍정적인 측면을 1-2가지 항목으로 요약합니다.
        4.  **개선점 (Cons)**: '주요 불만 사항'을 바탕으로 개선이 필요한 부분을 1-2가지 항목으로 요약합니다.

        결과는 반드시 마크다운 형식으로, 각 항목을 명확하게 구분하여 작성해야 합니다.
        """

        response = llm.invoke(prompt)
        return response.content.strip()
    except Exception as e:
        print(f"종합 평가 생성 중 오류: {e}")
        traceback.print_exc()
        return "종합 평가를 생성하는 데 실패했습니다."