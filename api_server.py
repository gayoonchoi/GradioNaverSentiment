import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import traceback

# 프로젝트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# temp_images 디렉토리 생성
os.makedirs("temp_images", exist_ok=True)

# 환경 설정
from src.config import setup_environment
setup_environment()

# 애플리케이션 임포트
from src.application.analysis_logic import (
    analyze_single_keyword_fully,
    perform_category_analysis
)
from src.data.festival_loader import (
    get_cat1_choices,
    get_cat2_choices,
    get_cat3_choices,
    get_festivals
)
from src.application.utils import create_driver
from src.application import seasonal_analysis
from src.infrastructure.reporting import seasonal_wordcloud

# FastAPI 앱 생성
app = FastAPI(
    title="GradioNaverSentiment API",
    description="Festival sentiment analysis API for festival planners",
    version="2.0.0"
)

# 이미지 파일 서빙
app.mount("/images", StaticFiles(directory="temp_images"), name="images")

# CORS 설정 (React 프론트엔드와 통신)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite 기본 포트
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 전역 WebDriver (재사용)
driver = None

@app.on_event("startup")
async def startup_event():
    """서버 시작 시 WebDriver 초기화"""
    global driver
    try:
        driver = create_driver()
        print("[OK] WebDriver initialized successfully")
    except Exception as e:
        print(f"[WARN] WebDriver initialization failed: {e}")
        driver = None

@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 WebDriver 정리"""
    global driver
    if driver:
        try:
            driver.quit()
            print("[OK] WebDriver closed")
        except:
            pass

# Pydantic 모델
class KeywordAnalysisRequest(BaseModel):
    keyword: str
    num_reviews: int = 10
    log_details: bool = True

class CategoryAnalysisRequest(BaseModel):
    cat1: str
    cat2: str
    cat3: str
    num_reviews: int = 10

class ComparisonRequest(BaseModel):
    keyword_a: str
    keyword_b: str
    num_reviews: int = 10

# ==================== 엔드포인트 ====================

@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "GradioNaverSentiment API",
        "status": "running",
        "version": "2.0.0",
        "description": "Festival sentiment analysis for planners"
    }

@app.get("/api/config/categories")
async def get_categories():
    """카테고리 1단계 목록 반환"""
    try:
        return {"categories": get_cat1_choices()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/categories/medium")
async def get_medium_categories(cat1: str):
    """카테고리 2단계 목록 반환"""
    try:
        return {"categories": get_cat2_choices(cat1)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/categories/small")
async def get_small_categories(cat1: str, cat2: str):
    """카테고리 3단계 목록 반환"""
    try:
        return {"categories": get_cat3_choices(cat1, cat2)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/festivals")
async def get_festival_list(cat1: str, cat2: str, cat3: str):
    """선택한 카테고리의 축제 목록 반환"""
    try:
        festivals = get_festivals(cat1, cat2, cat3)
        return {"festivals": festivals}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze/keyword")
async def analyze_keyword(request: KeywordAnalysisRequest):
    """
    단일 키워드 감성 분석

    Returns:
        - status: 분석 상태
        - total_pos/neg: 긍정/부정 문장 수
        - satisfaction_counts: 만족도 5단계 분포
        - distribution_interpretation: LLM 해석 텍스트
        - charts: 차트 데이터 (만족도, 이상치, 절대점수 등)
        - blog_results: 개별 블로그 분석 결과
        - seasonal_data: 계절별 데이터
    """
    global driver
    if not driver:
        driver = create_driver()

    try:
        print(f"📊 분석 시작: {request.keyword}, {request.num_reviews}개 리뷰")

        # 프로그레스 없이 직접 호출
        class DummyProgress:
            def __call__(self, *args, **kwargs):
                pass

        progress = DummyProgress()

        # analysis_logic.py의 함수 직접 호출
        results = analyze_single_keyword_fully(
            keyword=request.keyword,
            num_reviews=request.num_reviews,
            driver=driver,
            log_details=request.log_details,
            progress=progress,
            progress_desc="API 분석"
        )

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        # 결과를 API 응답 형식으로 변환
        response = {
            "status": results.get("status", "분석 완료"),
            "keyword": request.keyword,
            "total_pos": results.get("total_pos", 0),
            "total_neg": results.get("total_neg", 0),
            "avg_satisfaction": results.get("avg_satisfaction", 3.0),
            "satisfaction_counts": results.get("satisfaction_counts", {}),
            "distribution_interpretation": results.get("distribution_interpretation", ""),
            "all_scores": results.get("all_scores", []),
            "outliers": results.get("outliers", []),
            "seasonal_data": results.get("seasonal_data", {}),
            "blog_results": results.get("blog_results_df", {}).to_dict('records') if hasattr(results.get("blog_results_df"), 'to_dict') else [],
            "negative_summary": results.get("negative_summary", ""),
            "overall_summary": results.get("overall_summary", ""),
            "trend_metrics": results.get("trend_metrics", {}),
            "url_markdown": results.get("url_markdown", ""),
            "trend_graph": results.get("trend_graph"),
            "focused_trend_graph": results.get("focused_trend_graph"),
            "seasonal_word_clouds": results.get("seasonal_word_clouds"),
            # 상세 정보 테이블용 데이터 추가
            "addr1": results.get("addr1", "N/A"),
            "addr2": results.get("addr2", "N/A"),
            "areaCode": results.get("areaCode", "N/A"),
            "eventStartDate": results.get("festival_start_date").strftime('%Y-%m-%d') if results.get("festival_start_date") else "N/A",
            "eventEndDate": results.get("festival_end_date").strftime('%Y-%m-%d') if results.get("festival_end_date") else "N/A",
            "eventPeriod": results.get("event_period", "N/A"),
            "sentiment_score": results.get("total_sentiment_score", 0),
            "satisfaction_delta": results.get("satisfaction_delta", 0),
            "emotion_keyword_freq": results.get("emotion_keyword_freq", {})
        }

        print(f"[OK] 분석 완료: {request.keyword}")
        return response

    except Exception as e:
        print(f"[ERROR] 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

@app.post("/api/analyze/category")
async def analyze_category(request: CategoryAnalysisRequest):
    """
    카테고리별 축제 분석

    선택한 카테고리의 모든 축제를 분석하여 종합 결과 제공
    """
    global driver
    if not driver:
        driver = create_driver()

    try:
        print(f"📊 카테고리 분석 시작: {request.cat1} > {request.cat2} > {request.cat3}")

        class DummyProgress:
            def __call__(self, *args, **kwargs):
                pass

        progress = DummyProgress()

        results = perform_category_analysis(
            cat1=request.cat1,
            cat2=request.cat2,
            cat3=request.cat3,
            num_reviews=request.num_reviews,
            driver=driver,
            log_details=True,
            progress=progress,
            initial_progress=0,
            total_steps=1
        )

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        response = {
            "status": results.get("status", "분석 완료"),
            "category": f"{request.cat1} > {request.cat2} > {request.cat3}",
            "total_festivals": results.get("total_festivals", 0),
            "analyzed_festivals": results.get("analyzed_festivals", 0),
            "overall_summary": results.get("overall_summary_df", {}).to_dict('records') if hasattr(results.get("overall_summary_df"), 'to_dict') else [],
            "individual_results": results.get("individual_festival_results_df", {}).to_dict('records') if hasattr(results.get("individual_festival_results_df"), 'to_dict') else [],
            "seasonal_data": results.get("seasonal_data", {}),
        }

        print(f"[OK] 카테고리 분석 완료")
        return response

    except Exception as e:
        print(f"[ERROR] 카테고리 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

@app.post("/api/analyze/comparison")
async def analyze_comparison(request: ComparisonRequest):
    """
    2개 키워드 비교 분석
    """
    global driver
    if not driver:
        driver = create_driver()

    try:
        print(f"📊 비교 분석 시작: {request.keyword_a} vs {request.keyword_b}")

        class DummyProgress:
            def __call__(self, *args, **kwargs):
                pass

        progress = DummyProgress()

        # 두 키워드를 각각 분석
        results_a = analyze_single_keyword_fully(
            keyword=request.keyword_a,
            num_reviews=request.num_reviews,
            driver=driver,
            log_details=True,
            progress=progress,
            progress_desc="비교(A)"
        )

        results_b = analyze_single_keyword_fully(
            keyword=request.keyword_b,
            num_reviews=request.num_reviews,
            driver=driver,
            log_details=True,
            progress=progress,
            progress_desc="비교(B)"
        )

        if "error" in results_a:
            raise HTTPException(status_code=400, detail=f"축제 A 분석 실패: {results_a['error']}")
        if "error" in results_b:
            raise HTTPException(status_code=400, detail=f"축제 B 분석 실패: {results_b['error']}")

        response = {
            "status": "비교 분석 완료",
            "keyword_a": request.keyword_a,
            "keyword_b": request.keyword_b,
            "results_a": {
                "total_pos": results_a.get("total_pos", 0),
                "total_neg": results_a.get("total_neg", 0),
                "avg_satisfaction": results_a.get("avg_satisfaction", 3.0),
                "satisfaction_counts": results_a.get("satisfaction_counts", {}),
                "distribution_interpretation": results_a.get("distribution_interpretation", ""),
            },
            "results_b": {
                "total_pos": results_b.get("total_pos", 0),
                "total_neg": results_b.get("total_neg", 0),
                "avg_satisfaction": results_b.get("avg_satisfaction", 3.0),
                "satisfaction_counts": results_b.get("satisfaction_counts", {}),
                "distribution_interpretation": results_b.get("distribution_interpretation", ""),
            },
            "comparison_summary": f"{request.keyword_a}와 {request.keyword_b}의 비교 분석이 완료되었습니다.",
        }

        print(f"[OK] 비교 분석 완료")
        return response

    except Exception as e:
        print(f"[ERROR] 비교 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

@app.get("/api/seasonal/analyze")
async def analyze_seasonal_trends(season: str = Query(..., description="Season: 봄, 여름, 가을, 겨울")):
    """
    계절별 인기 축제 트렌드 분석

    Returns:
        - season: 선택한 계절
        - wordcloud_url: 워드클라우드 이미지 URL
        - timeline_url: 타임라인 그래프 이미지 URL
        - top_festivals: 상위 10개 축제 테이블 데이터
        - festival_names: 드롭다운용 축제명 리스트
    """
    try:
        print(f"📊 계절별 트렌드 분석 시작: {season}")

        # 1. 워드클라우드용 축제 빈도 데이터 (상위 120개)
        freq_dict = seasonal_analysis.get_festival_frequency_dict(season, top_n=120)

        # 2. 워드클라우드 이미지 생성
        wordcloud_path = seasonal_wordcloud.create_wordcloud_for_gradio(freq_dict, season)
        wordcloud_url = f"/images/{os.path.basename(wordcloud_path)}"

        # 3. 타임라인 그래프 생성
        timeline_path = seasonal_analysis.create_timeline_graph(season, top_n=10)
        timeline_url = f"/images/{os.path.basename(timeline_path)}"

        # 4. 테이블 데이터
        table_df = seasonal_analysis.get_table_data(season, top_n=10)

        # 5. 드롭다운용 축제명 리스트
        festival_names = seasonal_analysis.get_festival_names_for_season(season, top_n=10)

        response = {
            "status": "분석 완료",
            "season": season,
            "wordcloud_url": wordcloud_url,
            "timeline_url": timeline_url,
            "top_festivals": table_df.to_dict('records'),
            "festival_names": festival_names
        }

        print(f"[OK] 계절별 트렌드 분석 완료: {season}")
        return response

    except FileNotFoundError as e:
        print(f"[ERROR] 데이터 파일 없음: {e}")
        raise HTTPException(
            status_code=404,
            detail="트렌드 데이터를 찾을 수 없습니다. scripts/collect_sample_100.py를 먼저 실행해주세요."
        )
    except Exception as e:
        print(f"[ERROR] 계절별 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")

@app.get("/api/seasonal/festival-trend")
async def get_festival_trend(
    festival_name: str = Query(..., description="Festival name"),
    season: str = Query(None, description="Season (optional, for color selection)")
):
    """
    개별 축제의 검색 트렌드 그래프 조회

    Returns:
        - festival_name: 축제명
        - trend_graph_url: 트렌드 그래프 이미지 URL
    """
    try:
        print(f"📊 축제 트렌드 조회: {festival_name}")

        # 개별 축제 트렌드 그래프 생성
        trend_path = seasonal_analysis.create_individual_festival_trend_graph(festival_name, season)
        trend_url = f"/images/{os.path.basename(trend_path)}"

        response = {
            "status": "조회 완료",
            "festival_name": festival_name,
            "trend_graph_url": trend_url
        }

        print(f"[OK] 축제 트렌드 조회 완료: {festival_name}")
        return response

    except ValueError as e:
        print(f"[ERROR] 축제 찾기 실패: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"[ERROR] 트렌드 조회 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"조회 중 오류 발생: {str(e)}")

# 서버 실행
if __name__ == "__main__":
    print("[START] GradioNaverSentiment API Server Starting...")
    print("[INFO] Swagger UI: http://localhost:8001/docs")
    print("[INFO] Frontend: http://localhost:5173 (Vite)")
    uvicorn.run(app, host="0.0.0.0", port=8001)
