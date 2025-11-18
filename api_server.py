import os
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import functools
import uvicorn
import traceback
import asyncio
import json
from fastapi.responses import StreamingResponse

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
    perform_category_analysis,
)
from src.data.festival_loader import (
    get_cat1_choices,
    get_cat2_choices,
    get_cat3_choices,
    get_festivals,
)
from src.application.utils import (
    create_driver,
    load_cached_analysis,
    save_analysis_to_cache,
    generate_recommendation_analysis,
    generate_comparison_recommendation,
)
from src.application import seasonal_analysis
from src.infrastructure.reporting import seasonal_wordcloud

# FastAPI 앱 생성
app = FastAPI(
    title="GradioNaverSentiment API",
    description="Festival sentiment analysis API for festival planners",
    version="2.0.0",
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


# 캐싱을 지원하는 분석 헬퍼 함수
def analyze_with_cache(
    keyword: str,
    num_reviews: int,
    log_details: bool = True,
    progress_desc: str = "분석",
) -> dict:
    """캐싱을 지원하는 키워드 분석 함수"""
    global driver

    # 1. 캐시 확인
    cached_results = load_cached_analysis(keyword, num_reviews)
    if cached_results:
        print(f"[CACHE HIT] 캐시된 결과 사용: {keyword}")
        return cached_results

    # 2. 캐시가 없으면 새로운 분석 실행
    print(f"[CACHE MISS] 새로운 분석 실행: {keyword}")
    if not driver:
        driver = create_driver()

    class DummyProgress:
        def __call__(self, *args, **kwargs):
            pass

    progress = DummyProgress()

    results = analyze_single_keyword_fully(
        keyword=keyword,
        num_reviews=num_reviews,
        driver=driver,
        log_details=log_details,
        progress=progress,
        progress_desc=progress_desc,
    )

    if "error" in results:
        return results

    # 3. API 응답 형식으로 변환
    response = {
        "status": results.get("status", "분석 완료"),
        "keyword": keyword,
        "total_pos": results.get("total_pos", 0),
        "total_neg": results.get("total_neg", 0),
        "avg_satisfaction": results.get("avg_satisfaction", 3.0),
        "satisfaction_counts": results.get("satisfaction_counts", {}),
        "distribution_interpretation": results.get("distribution_interpretation", ""),
        "all_scores": results.get("all_scores", []),
        "outliers": results.get("outliers", []),
        "seasonal_data": results.get("seasonal_data", {}),
        "blog_results": (
            results.get("blog_results_df", {}).to_dict("records")
            if hasattr(results.get("blog_results_df"), "to_dict")
            else []
        ),
        "negative_summary": results.get("negative_summary", ""),
        "overall_summary": results.get("overall_summary", ""),
        "trend_metrics": results.get("trend_metrics", {}),
        "url_markdown": results.get("url_markdown", ""),
        "trend_graph": results.get("trend_graph"),
        "focused_trend_graph": results.get("focused_trend_graph"),
        "seasonal_word_clouds": results.get("seasonal_word_clouds"),
        "addr1": results.get("addr1", "N/A"),
        "addr2": results.get("addr2", "N/A"),
        "areaCode": results.get("areaCode", "N/A"),
        "eventStartDate": (
            results.get("festival_start_date").strftime("%Y-%m-%d")
            if results.get("festival_start_date")
            else "N/A"
        ),
        "eventEndDate": (
            results.get("festival_end_date").strftime("%Y-%m-%d")
            if results.get("festival_end_date")
            else "N/A"
        ),
        "eventPeriod": results.get("event_period", "N/A"),
        "sentiment_score": results.get("total_sentiment_score", 0),
        "satisfaction_delta": results.get("satisfaction_delta", 0),
        "emotion_keyword_freq": results.get("emotion_keyword_freq", {}),
    }

    # 4. 캐시에 저장
    save_analysis_to_cache(keyword, num_reviews, response)

    return response


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


class CategoryComparisonRequest(BaseModel):
    cat1_a: str
    cat2_a: str
    cat3_a: str
    cat1_b: str
    cat2_b: str
    cat3_b: str
    num_reviews: int = 10


class SingleRecommendationRequest(BaseModel):
    keyword: str
    num_reviews: int = 10
    region: str
    season: str


class ComparisonRecommendationRequest(BaseModel):
    keyword_a: str
    keyword_b: str
    num_reviews: int = 10
    region: str
    season: str


class CategoryRecommendationRequest(BaseModel):
    cat1: str
    cat2: str
    cat3: str
    num_reviews: int = 10
    region: str
    season: str


class CategoryComparisonRecommendationRequest(BaseModel):
    cat1_a: str
    cat2_a: str
    cat3_a: str
    cat1_b: str
    cat2_b: str
    cat3_b: str
    num_reviews: int = 10
    region: str
    season: str


# ==================== 엔드포인트 ====================


@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "GradioNaverSentiment API",
        "status": "running",
        "version": "2.0.0",
        "description": "Festival sentiment analysis for planners",
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
    try:
        print(f"📊 분석 시작: {request.keyword}, {request.num_reviews}개 리뷰")

        # 캐싱을 지원하는 분석 수행
        response = analyze_with_cache(
            keyword=request.keyword,
            num_reviews=request.num_reviews,
            log_details=request.log_details,
            progress_desc="API 분석",
        )

        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])

        print(f"[OK] 분석 완료: {request.keyword}")
        return response

    except HTTPException:
        raise
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
        print(
            f"📊 카테고리 분석 시작: {request.cat1} > {request.cat2} > {request.cat3}"
        )

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
            total_steps=1,
        )

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        response = {
            "status": results.get("status", "분석 완료"),
            "category": f"{request.cat1} > {request.cat2} > {request.cat3}",
            "total_festivals": results.get("total_festivals", 0),
            "analyzed_festivals": results.get("analyzed_festivals", 0),
            "total_pos": results.get("total_pos", 0),
            "total_neg": results.get("total_neg", 0),
            "individual_results": (
                results.get("individual_festival_results_df", {}).to_dict("records")
                if hasattr(results.get("individual_festival_results_df"), "to_dict")
                else []
            ),
            "seasonal_data": results.get("seasonal_data", {}),
            "category_overall_summary": results.get("category_overall_summary", ""),
            "category_negative_summary": results.get("category_negative_summary", ""),
            "seasonal_word_clouds": results.get("category_seasonal_word_clouds", {}),
            "keyword_wordclouds": results.get(
                "category_keyword_wordclouds", {}
            ),  # 블로그 기반 키워드 빈도수 워드클라우드
            # 신규 추가된 종합 분석 데이터
            "all_scores": results.get("all_scores", []),
            "satisfaction_counts": results.get("satisfaction_counts", {}),
            "avg_satisfaction": results.get("avg_satisfaction", 3.0),
            "distribution_interpretation": results.get(
                "distribution_interpretation", ""
            ),
            "outliers": results.get("outliers", []),
            "trend_graph": results.get("trend_graph"),
            "focused_trend_graph": results.get("focused_trend_graph"),
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
    try:
        print(f"📊 비교 분석 시작: {request.keyword_a} vs {request.keyword_b}")

        # 두 키워드를 각각 캐싱 지원 분석 수행
        results_a = analyze_with_cache(
            keyword=request.keyword_a,
            num_reviews=request.num_reviews,
            log_details=True,
            progress_desc="비교(A)",
        )

        results_b = analyze_with_cache(
            keyword=request.keyword_b,
            num_reviews=request.num_reviews,
            log_details=True,
            progress_desc="비교(B)",
        )

        if "error" in results_a:
            raise HTTPException(
                status_code=400, detail=f"축제 A 분석 실패: {results_a['error']}"
            )
        if "error" in results_b:
            raise HTTPException(
                status_code=400, detail=f"축제 B 분석 실패: {results_b['error']}"
            )

        response = {
            "status": "비교 분석 완료",
            "keyword_a": request.keyword_a,
            "keyword_b": request.keyword_b,
            "results_a": {
                "total_pos": results_a.get("total_pos", 0),
                "total_neg": results_a.get("total_neg", 0),
                "avg_satisfaction": results_a.get("avg_satisfaction", 3.0),
                "satisfaction_counts": results_a.get("satisfaction_counts", {}),
                "distribution_interpretation": results_a.get(
                    "distribution_interpretation", ""
                ),
            },
            "results_b": {
                "total_pos": results_b.get("total_pos", 0),
                "total_neg": results_b.get("total_neg", 0),
                "avg_satisfaction": results_b.get("avg_satisfaction", 3.0),
                "satisfaction_counts": results_b.get("satisfaction_counts", {}),
                "distribution_interpretation": results_b.get(
                    "distribution_interpretation", ""
                ),
            },
            "comparison_summary": f"{request.keyword_a}와 {request.keyword_b}의 비교 분석이 완료되었습니다.",
        }

        print(f"[OK] 비교 분석 완료")
        return response

    except Exception as e:
        print(f"[ERROR] 비교 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.post("/api/analyze/category-comparison")
async def analyze_category_comparison(request: CategoryComparisonRequest):
    """
    카테고리 비교 분석 (병렬 처리)

    두 개의 카테고리를 동시에 분석하여 시간 절약
    """
    global driver
    if not driver:
        driver = create_driver()

    try:
        category_a = f"{request.cat1_a} > {request.cat2_a} > {request.cat3_a}"
        category_b = f"{request.cat1_b} > {request.cat2_b} > {request.cat3_b}"
        print(f"📊 카테고리 비교 분석 시작 (병렬 처리): {category_a} vs {category_b}")

        class DummyProgress:
            def __call__(self, *args, **kwargs):
                pass

        progress = DummyProgress()

        # 병렬로 두 카테고리 동시 분석
        async def analyze_category_a():
            import asyncio

            return await asyncio.to_thread(
                perform_category_analysis,
                cat1=request.cat1_a,
                cat2=request.cat2_a,
                cat3=request.cat3_a,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress,
                initial_progress=0,
                total_steps=1,
            )

        async def analyze_category_b():
            import asyncio

            return await asyncio.to_thread(
                perform_category_analysis,
                cat1=request.cat1_b,
                cat2=request.cat2_b,
                cat3=request.cat3_b,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress,
                initial_progress=0,
                total_steps=1,
            )

        # 두 작업을 동시에 실행
        import asyncio

        results_a, results_b = await asyncio.gather(
            analyze_category_a(), analyze_category_b()
        )

        if "error" in results_a:
            raise HTTPException(
                status_code=400, detail=f"카테고리 A 분석 실패: {results_a['error']}"
            )
        if "error" in results_b:
            raise HTTPException(
                status_code=400, detail=f"카테고리 B 분석 실패: {results_b['error']}"
            )

        response = {
            "status": "카테고리 비교 분석 완료 (병렬 처리)",
            "category_a": category_a,
            "category_b": category_b,
            "results_a": {
                "total_festivals": results_a.get("total_festivals", 0),
                "analyzed_festivals": results_a.get("analyzed_festivals", 0),
                "total_pos": results_a.get("total_pos", 0),
                "total_neg": results_a.get("total_neg", 0),
                "avg_satisfaction": results_a.get("avg_satisfaction", 3.0),
                "satisfaction_counts": results_a.get("satisfaction_counts", {}),
                "seasonal_data": results_a.get("seasonal_data", {}),
                "category_overall_summary": results_a.get(
                    "category_overall_summary", ""
                ),
                "distribution_interpretation": results_a.get(
                    "distribution_interpretation", ""
                ),
            },
            "results_b": {
                "total_festivals": results_b.get("total_festivals", 0),
                "analyzed_festivals": results_b.get("analyzed_festivals", 0),
                "total_pos": results_b.get("total_pos", 0),
                "total_neg": results_b.get("total_neg", 0),
                "avg_satisfaction": results_b.get("avg_satisfaction", 3.0),
                "satisfaction_counts": results_b.get("satisfaction_counts", {}),
                "seasonal_data": results_b.get("seasonal_data", {}),
                "category_overall_summary": results_b.get(
                    "category_overall_summary", ""
                ),
                "distribution_interpretation": results_b.get(
                    "distribution_interpretation", ""
                ),
            },
            "comparison_summary": f"{category_a}와 {category_b}의 카테고리 비교 분석이 완료되었습니다.",
        }

        print(f"[OK] 카테고리 비교 분석 완료 (병렬 처리)")
        return response

    except Exception as e:
        print(f"[ERROR] 카테고리 비교 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.post("/api/recommend/single")
async def recommend_single_analysis(request: SingleRecommendationRequest):
    """
    단일 축제 분석 결과를 바탕으로 지역과 계절을 고려한 AI 추천 분석

    Args:
        keyword: 축제명
        num_reviews: 분석할 리뷰 수
        region: 사용자 지역 (예: 서울, 부산)
        season: 사용자 계절 (예: 봄, 여름, 가을, 겨울)

    Returns:
        recommendation: AI 추천 분석 텍스트 (마크다운 형식)
    """
    try:
        print(
            f"🤖 AI 추천 분석 시작: {request.keyword} ({request.region}, {request.season})"
        )

        # 1. 기존 분석 결과 가져오기 (캐싱 지원)
        analysis_result = analyze_with_cache(
            keyword=request.keyword,
            num_reviews=request.num_reviews,
            log_details=True,
            progress_desc="추천 분석",
        )

        if "error" in analysis_result:
            raise HTTPException(status_code=400, detail=analysis_result["error"])

        # 2. AI 추천 분석 생성
        recommendation = generate_recommendation_analysis(
            analysis_result=analysis_result,
            region=request.region,
            season=request.season,
        )

        response = {
            "status": "추천 분석 완료",
            "keyword": request.keyword,
            "region": request.region,
            "season": request.season,
            "recommendation": recommendation,
        }

        print(f"[OK] AI 추천 분석 완료: {request.keyword}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] AI 추천 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"추천 분석 중 오류 발생: {str(e)}")


@app.post("/api/recommend/category")
async def recommend_category_analysis(request: CategoryRecommendationRequest):
    """
    카테고리 분석 결과를 바탕으로 지역과 계절을 고려한 AI 추천 분석
    """
    global driver
    if not driver:
        driver = create_driver()

    try:
        category = f"{request.cat1} > {request.cat2} > {request.cat3}"
        print(
            f"🤖 AI 카테고리 추천 분석 시작: {category} ({request.region}, {request.season})"
        )

        # 1. 카테고리 분석 실행
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
            total_steps=1,
        )

        if "error" in results:
            raise HTTPException(status_code=400, detail=results["error"])

        # 2. API 응답 형식으로 변환
        analysis_result = {
            "keyword": category,
            "total_pos": results.get("total_pos", 0),
            "total_neg": results.get("total_neg", 0),
            "avg_satisfaction": results.get("avg_satisfaction", 3.0),
            "sentiment_score": (
                results.get("total_pos", 0) - results.get("total_neg", 0)
            )
            / max(results.get("total_pos", 0) + results.get("total_neg", 0), 1),
            "trend_metrics": {"trend_index": 0},  # 카테고리는 트렌드 지수 없음
            "negative_summary": results.get("category_negative_summary", ""),
        }

        # 3. AI 추천 분석 생성
        recommendation = generate_recommendation_analysis(
            analysis_result=analysis_result,
            region=request.region,
            season=request.season,
        )

        response = {
            "status": "카테고리 추천 분석 완료",
            "category": category,
            "region": request.region,
            "season": request.season,
            "recommendation": recommendation,
        }

        print(f"[OK] AI 카테고리 추천 분석 완료: {category}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] AI 카테고리 추천 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"추천 분석 중 오류 발생: {str(e)}")


@app.post("/api/recommend/comparison")
async def recommend_comparison_analysis(request: ComparisonRecommendationRequest):
    """
    2개 축제 비교 분석 결과를 바탕으로 지역과 계절을 고려한 AI 비교 추천 분석
    """
    try:
        print(
            f"🤖 AI 비교 추천 분석 시작: {request.keyword_a} vs {request.keyword_b} ({request.region}, {request.season})"
        )

        # 1. 두 축제 분석 결과 가져오기
        results_a = analyze_with_cache(
            keyword=request.keyword_a,
            num_reviews=request.num_reviews,
            log_details=True,
            progress_desc="비교 추천(A)",
        )

        results_b = analyze_with_cache(
            keyword=request.keyword_b,
            num_reviews=request.num_reviews,
            log_details=True,
            progress_desc="비교 추천(B)",
        )

        if "error" in results_a:
            raise HTTPException(
                status_code=400, detail=f"축제 A 분석 실패: {results_a['error']}"
            )
        if "error" in results_b:
            raise HTTPException(
                status_code=400, detail=f"축제 B 분석 실패: {results_b['error']}"
            )

        # 2. AI 비교 추천 분석 생성
        recommendation = generate_comparison_recommendation(
            results_a=results_a,
            results_b=results_b,
            name_a=request.keyword_a,
            name_b=request.keyword_b,
            region=request.region,
            season=request.season,
        )

        response = {
            "status": "비교 추천 분석 완료",
            "keyword_a": request.keyword_a,
            "keyword_b": request.keyword_b,
            "region": request.region,
            "season": request.season,
            "recommendation": recommendation,
        }

        print(f"[OK] AI 비교 추천 분석 완료")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] AI 비교 추천 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"추천 분석 중 오류 발생: {str(e)}")


@app.post("/api/recommend/category-comparison")
async def recommend_category_comparison_analysis(
    request: CategoryComparisonRecommendationRequest,
):
    """
    카테고리 비교 분석 결과를 바탕으로 지역과 계절을 고려한 AI 비교 추천 분석 (병렬 처리)
    """
    global driver
    if not driver:
        driver = create_driver()

    try:
        category_a = f"{request.cat1_a} > {request.cat2_a} > {request.cat3_a}"
        category_b = f"{request.cat1_b} > {request.cat2_b} > {request.cat3_b}"
        print(
            f"🤖 AI 카테고리 비교 추천 분석 시작: {category_a} vs {category_b} ({request.region}, {request.season})"
        )

        class DummyProgress:
            def __call__(self, *args, **kwargs):
                pass

        progress = DummyProgress()

        # 1. 병렬로 두 카테고리 동시 분석
        async def analyze_category_a():
            import asyncio

            return await asyncio.to_thread(
                perform_category_analysis,
                cat1=request.cat1_a,
                cat2=request.cat2_a,
                cat3=request.cat3_a,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress,
                initial_progress=0,
                total_steps=1,
            )

        async def analyze_category_b():
            import asyncio

            return await asyncio.to_thread(
                perform_category_analysis,
                cat1=request.cat1_b,
                cat2=request.cat2_b,
                cat3=request.cat3_b,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress,
                initial_progress=0,
                total_steps=1,
            )

        import asyncio

        results_a, results_b = await asyncio.gather(
            analyze_category_a(), analyze_category_b()
        )

        if "error" in results_a:
            raise HTTPException(
                status_code=400, detail=f"카테고리 A 분석 실패: {results_a['error']}"
            )
        if "error" in results_b:
            raise HTTPException(
                status_code=400, detail=f"카테고리 B 분석 실패: {results_b['error']}"
            )

        # 2. API 응답 형식으로 변환
        formatted_a = {
            "keyword": category_a,
            "total_pos": results_a.get("total_pos", 0),
            "total_neg": results_a.get("total_neg", 0),
            "avg_satisfaction": results_a.get("avg_satisfaction", 3.0),
            "sentiment_score": (
                results_a.get("total_pos", 0) - results_a.get("total_neg", 0)
            )
            / max(results_a.get("total_pos", 0) + results_a.get("total_neg", 0), 1),
            "trend_metrics": {"trend_index": 0},
            "negative_summary": results_a.get("category_negative_summary", ""),
        }

        formatted_b = {
            "keyword": category_b,
            "total_pos": results_b.get("total_pos", 0),
            "total_neg": results_b.get("total_neg", 0),
            "avg_satisfaction": results_b.get("avg_satisfaction", 3.0),
            "sentiment_score": (
                results_b.get("total_pos", 0) - results_b.get("total_neg", 0)
            )
            / max(results_b.get("total_pos", 0) + results_b.get("total_neg", 0), 1),
            "trend_metrics": {"trend_index": 0},
            "negative_summary": results_b.get("category_negative_summary", ""),
        }

        # 3. AI 비교 추천 분석 생성
        recommendation = generate_comparison_recommendation(
            results_a=formatted_a,
            results_b=formatted_b,
            name_a=category_a,
            name_b=category_b,
            region=request.region,
            season=request.season,
        )

        response = {
            "status": "카테고리 비교 추천 분석 완료",
            "category_a": category_a,
            "category_b": category_b,
            "region": request.region,
            "season": request.season,
            "recommendation": recommendation,
        }

        print(f"[OK] AI 카테고리 비교 추천 분석 완료")
        return response

    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] AI 카테고리 비교 추천 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"추천 분석 중 오류 발생: {str(e)}")


@app.get("/api/seasonal/analyze")
async def analyze_seasonal_trends(
    season: str = Query(..., description="Season: 봄, 여름, 가을, 겨울")
):
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
        wordcloud_path = seasonal_wordcloud.create_wordcloud_for_gradio(
            freq_dict, season
        )
        wordcloud_url = f"/images/{os.path.basename(wordcloud_path)}"

        # 3. 타임라인 그래프 생성
        timeline_path = seasonal_analysis.create_timeline_graph(season, top_n=10)
        timeline_url = f"/images/{os.path.basename(timeline_path)}"

        # 4. 테이블 데이터
        table_df = seasonal_analysis.get_table_data(season, top_n=10)

        # 5. 드롭다운용 축제명 리스트
        festival_names = seasonal_analysis.get_festival_names_for_season(
            season, top_n=10
        )

        response = {
            "status": "분석 완료",
            "season": season,
            "wordcloud_url": wordcloud_url,
            "timeline_url": timeline_url,
            "top_festivals": table_df.to_dict("records"),
            "festival_names": festival_names,
        }

        print(f"[OK] 계절별 트렌드 분석 완료: {season}")
        return response

    except FileNotFoundError as e:
        print(f"[ERROR] 데이터 파일 없음: {e}")
        raise HTTPException(
            status_code=404,
            detail="트렌드 데이터를 찾을 수 없습니다. scripts/collect_sample_100.py를 먼저 실행해주세요.",
        )
    except Exception as e:
        print(f"[ERROR] 계절별 분석 중 오류: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"분석 중 오류 발생: {str(e)}")


@app.get("/api/seasonal/festival-trend")
async def get_festival_trend(
    festival_name: str = Query(..., description="Festival name"),
    season: str = Query(None, description="Season (optional, for color selection)"),
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
        trend_path = seasonal_analysis.create_individual_festival_trend_graph(
            festival_name, season
        )
        trend_url = f"/images/{os.path.basename(trend_path)}"

        response = {
            "status": "조회 완료",
            "festival_name": festival_name,
            "trend_graph_url": trend_url,
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


# ==================== 스트리밍 엔드포인트 ====================


class ProgressCallback:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    def __call__(self, percent, desc=""):
        try:
            # 이벤트 루프가 실행 중인지 확인하고, 실행 중이면 큐에 작업을 넣습니다.
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(
                self.queue.put_nowait,
                {"type": "progress", "percent": percent, "message": desc},
            )
        except RuntimeError:
            # 이벤트 루프가 없는 경우 (예: 테스트 환경)
            self.queue.put_nowait(
                {"type": "progress", "percent": percent, "message": desc}
            )


async def run_analysis_in_thread(target_func, *args, **kwargs):
    """분석 함수를 별도 스레드에서 실행하고 결과를 반환합니다."""
    loop = asyncio.get_running_loop()
    # Use functools.partial to wrap the function and its arguments
    p = functools.partial(target_func, *args, **kwargs)
    return await loop.run_in_executor(None, p)


def format_sse_message(data: dict) -> str:
    """주어진 데이터를 SSE 메시지 형식으로 변환합니다."""
    json_data = json.dumps(data, ensure_ascii=False)
    return f"data: {json_data}\n\n"


def format_single_keyword_response(results: dict, keyword: str) -> dict:
    """analyze_single_keyword_fully 결과를 API 응답 형식으로 변환합니다."""
    return {
        "status": results.get("status", "분석 완료"),
        "keyword": keyword,
        "total_pos": results.get("total_pos", 0),
        "total_neg": results.get("total_neg", 0),
        "avg_satisfaction": results.get("avg_satisfaction", 3.0),
        "satisfaction_counts": results.get("satisfaction_counts", {}),
        "distribution_interpretation": results.get("distribution_interpretation", ""),
        "all_scores": results.get("all_scores", []),
        "outliers": results.get("outliers", []),
        "seasonal_data": results.get("seasonal_data", {}),
        "blog_results": (
            results.get("blog_results_df", {}).to_dict("records")
            if hasattr(results.get("blog_results_df"), "to_dict")
            else []
        ),
        "negative_summary": results.get("negative_summary", ""),
        "overall_summary": results.get("overall_summary", ""),
        "trend_metrics": results.get("trend_metrics", {}),
        "url_markdown": results.get("url_markdown", ""),
        "trend_graph": results.get("trend_graph"),
        "focused_trend_graph": results.get("focused_trend_graph"),
        "seasonal_word_clouds": results.get("seasonal_word_clouds"),
        "addr1": results.get("addr1", "N/A"),
        "addr2": results.get("addr2", "N/A"),
        "areaCode": results.get("areaCode", "N/A"),
        "eventStartDate": (
            results.get("festival_start_date").strftime("%Y-%m-%d")
            if results.get("festival_start_date")
            else "N/A"
        ),
        "eventEndDate": (
            results.get("festival_end_date").strftime("%Y-%m-%d")
            if results.get("festival_end_date")
            else "N/A"
        ),
        "eventPeriod": results.get("event_period", "N/A"),
        "sentiment_score": results.get("total_sentiment_score", 0),
        "satisfaction_delta": results.get("satisfaction_delta", 0),
        "emotion_keyword_freq": results.get("emotion_keyword_freq", {}),
    }


# 1. --- `format_category_response` 정의 수정 ---
def format_category_response(results: dict, cat1: str, cat2: str, cat3: str) -> dict:
    """perform_category_analysis 결과를 API 응답 형식으로 변환합니다."""
    return {
        "status": results.get("status", "분석 완료"),
        "category": f"{cat1} > {cat2} > {cat3}",
        "total_festivals": results.get("total_festivals", 0),
        "analyzed_festivals": results.get("analyzed_festivals", 0),
        "total_pos": results.get("total_pos", 0),
        "total_neg": results.get("total_neg", 0),
        "individual_results": (
            results.get("individual_festival_results_df", {}).to_dict("records")
            if hasattr(results.get("individual_festival_results_df"), "to_dict")
            else []
        ),
        "seasonal_data": results.get("seasonal_data", {}),
        "category_overall_summary": results.get("category_overall_summary", ""),
        "category_negative_summary": results.get("category_negative_summary", ""),
        "seasonal_word_clouds": results.get("category_seasonal_word_clouds", {}),
        "keyword_wordclouds": results.get("category_keyword_wordclouds", {}),
        "all_scores": results.get("all_scores", []),
        "satisfaction_counts": results.get("satisfaction_counts", {}),
        "avg_satisfaction": results.get("avg_satisfaction", 3.0),
        "distribution_interpretation": results.get("distribution_interpretation", ""),
        "outliers": results.get("outliers", []),
        "trend_graph": results.get("trend_graph"),
        "focused_trend_graph": results.get("focused_trend_graph"),
    }


@app.post("/api/analyze/keyword/stream")
async def analyze_keyword_stream(request: KeywordAnalysisRequest):
    """단일 키워드 감성 분석 (스트리밍)"""

    cached_results = load_cached_analysis(request.keyword, request.num_reviews)
    if cached_results:

        async def single_result_stream():
            yield format_sse_message(
                {"type": "progress", "percent": 1, "message": "캐시된 결과 로드 완료"}
            )
            yield format_sse_message({"type": "result", "data": cached_results})

        return StreamingResponse(single_result_stream(), media_type="text/event-stream")

    queue = asyncio.Queue()
    progress_callback = ProgressCallback(queue)

    async def analysis_generator():
        global driver
        if not driver:
            driver = create_driver()

        yield format_sse_message(
            {"type": "progress", "percent": 0, "message": "분석 시작..."}
        )

        analysis_task = asyncio.create_task(
            run_analysis_in_thread(
                analyze_single_keyword_fully,
                keyword=request.keyword,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=request.log_details,
                progress=progress_callback,
                progress_desc="스트리밍 분석",
            )
        )

        while not analysis_task.done():
            try:
                message = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield format_sse_message(message)
            except asyncio.TimeoutError:
                await asyncio.sleep(0.1)
                continue

        results = await analysis_task

        if "error" in results:
            yield format_sse_message({"type": "error", "message": results["error"]})
        else:
            response = format_single_keyword_response(results, request.keyword)
            save_analysis_to_cache(request.keyword, request.num_reviews, response)
            yield format_sse_message({"type": "result", "data": response})

    return StreamingResponse(analysis_generator(), media_type="text/event-stream")


@app.post("/api/analyze/comparison/stream")
async def analyze_comparison_stream(request: ComparisonRequest):
    """2개 키워드 비교 분석 (스트리밍)"""
    queue_a = asyncio.Queue()
    queue_b = asyncio.Queue()
    progress_a = ProgressCallback(queue_a)
    progress_b = ProgressCallback(queue_b)

    async def analysis_generator():
        global driver
        if not driver:
            driver = create_driver()

        yield format_sse_message(
            {"type": "progress", "percent": 0, "message": "비교 분석 시작..."}
        )

        task_a = asyncio.create_task(
            run_analysis_in_thread(
                analyze_with_cache,
                keyword=request.keyword_a,
                num_reviews=request.num_reviews,
                log_details=True,
                progress_desc=f"{request.keyword_a} 분석",
            )
        )
        task_b = asyncio.create_task(
            run_analysis_in_thread(
                analyze_with_cache,
                keyword=request.keyword_b,
                num_reviews=request.num_reviews,
                log_details=True,
                progress_desc=f"{request.keyword_b} 분석",
            )
        )

        # For comparison, we don't have fine-grained progress, so we'll just wait
        results_a, results_b = await asyncio.gather(task_a, task_b)

        if "error" in results_a or "error" in results_b:
            error_msg = results_a.get("error", "") or results_b.get("error", "")
            yield format_sse_message({"type": "error", "message": error_msg})
            return

        # AI를 사용한 비교 요약 생성
        comparison_summary = generate_comparison_recommendation(
            results_a=results_a,
            results_b=results_b,
            name_a=request.keyword_a,
            name_b=request.keyword_b,
            region="전국",  # 비교 요약에서는 특정 지역/계절을 가정하지 않음
            season="전시즌",
        )

        response = {
            "status": "비교 분석 완료",
            "keyword_a": request.keyword_a,
            "keyword_b": request.keyword_b,
            "results_a": results_a,
            "results_b": results_b,
            "comparison_summary": comparison_summary,
        }
        yield format_sse_message(
            {"type": "progress", "percent": 1, "message": "분석 완료"}
        )
        yield format_sse_message({"type": "result", "data": response})

    return StreamingResponse(analysis_generator(), media_type="text/event-stream")


@app.post("/api/analyze/category/stream")
async def analyze_category_stream(request: CategoryAnalysisRequest):
    """카테고리별 축제 분석 (스트리밍)"""
    queue = asyncio.Queue()
    progress_callback = ProgressCallback(queue)

    async def analysis_generator():
        global driver
        if not driver:
            driver = create_driver()

        yield format_sse_message(
            {"type": "progress", "percent": 0, "message": "카테고리 분석 시작..."}
        )

        analysis_task = asyncio.create_task(
            run_analysis_in_thread(
                perform_category_analysis,
                cat1=request.cat1,
                cat2=request.cat2,
                cat3=request.cat3,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress_callback,
                initial_progress=0,
                total_steps=1,
            )
        )

        while not analysis_task.done():
            try:
                message = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield format_sse_message(message)
            except asyncio.TimeoutError:
                await asyncio.sleep(0.1)
                continue

        results = await analysis_task

        if "error" in results:
            yield format_sse_message({"type": "error", "message": results["error"]})
        else:
            # 2. --- `/api/analyze/category/stream` 호출 수정 ---
            response = format_category_response(
                results, request.cat1, request.cat2, request.cat3
            )
            yield format_sse_message({"type": "result", "data": response})

    return StreamingResponse(analysis_generator(), media_type="text/event-stream")


@app.post("/api/analyze/category-comparison/stream")
async def analyze_category_comparison_stream(request: CategoryComparisonRequest):
    """카테고리 비교 분석 (스트리밍)"""
    queue_a = asyncio.Queue()
    queue_b = asyncio.Queue()
    progress_a = ProgressCallback(queue_a)
    progress_b = ProgressCallback(queue_b)

    category_a_name = f"{request.cat1_a}>{request.cat2_a}>{request.cat3_a}"
    category_b_name = f"{request.cat1_b}>{request.cat2_b}>{request.cat3_b}"

    async def analysis_generator():
        global driver
        if not driver:
            driver = create_driver()

        yield format_sse_message(
            {"type": "progress", "percent": 0, "message": "카테고리 비교 분석 시작..."}
        )

        task_a = asyncio.create_task(
            run_analysis_in_thread(
                perform_category_analysis,
                cat1=request.cat1_a,
                cat2=request.cat2_a,
                cat3=request.cat3_a,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress_a,
                initial_progress=0,
                total_steps=1,
            )
        )
        task_b = asyncio.create_task(
            run_analysis_in_thread(
                perform_category_analysis,
                cat1=request.cat1_b,
                cat2=request.cat2_b,
                cat3=request.cat3_b,
                num_reviews=request.num_reviews,
                driver=driver,
                log_details=True,
                progress=progress_b,
                initial_progress=0,
                total_steps=1,
            )
        )

        percent_a, percent_b = 0, 0
        message_a, message_b = "대기 중...", "대기 중..."

        while not task_a.done() or not task_b.done():
            try:
                msg_a = (
                    await asyncio.wait_for(queue_a.get(), timeout=0.05)
                    if not task_a.done()
                    else None
                )
                if msg_a:
                    percent_a = msg_a.get("percent", 0)
                    message_a = msg_a.get("message", "")
            except asyncio.TimeoutError:
                pass

            try:
                msg_b = (
                    await asyncio.wait_for(queue_b.get(), timeout=0.05)
                    if not task_b.done()
                    else None
                )
                if msg_b:
                    percent_b = msg_b.get("percent", 0)
                    message_b = msg_b.get("message", "")
            except asyncio.TimeoutError:
                pass

            total_percent = (percent_a * 0.5) + (percent_b * 0.5)
            combined_message = f"[A: {category_a_name[:15]}...] {message_a}\n[B: {category_b_name[:15]}...] {message_b}"
            yield format_sse_message(
                {
                    "type": "progress",
                    "percent": total_percent,
                    "message": combined_message,
                }
            )
            await asyncio.sleep(0.1)

        results_a, results_b = await asyncio.gather(task_a, task_b)

        if "error" in results_a or "error" in results_b:
            error_msg = results_a.get("error", "") or results_b.get("error", "")
            yield format_sse_message({"type": "error", "message": error_msg})
            return

        # 3. --- `/api/analyze/category-comparison/stream` 호출 수정 ---
        formatted_a = format_category_response(
            results_a, request.cat1_a, request.cat2_a, request.cat3_a
        )
        formatted_b = format_category_response(
            results_b, request.cat1_b, request.cat2_b, request.cat3_b
        )

        # AI를 사용한 비교 요약 생성
        comparison_summary = generate_comparison_recommendation(
            results_a=formatted_a,
            results_b=formatted_b,
            name_a=category_a_name,
            name_b=category_b_name,
            region="전국",
            season="전시즌",
        )

        response = {
            "status": "카테고리 비교 분석 완료",
            "category_a": category_a_name,
            "category_b": category_b_name,
            "results_a": formatted_a,
            "results_b": formatted_b,
            "comparison_summary": comparison_summary,
        }
        yield format_sse_message(
            {"type": "progress", "percent": 1, "message": "분석 완료"}
        )
        yield format_sse_message({"type": "result", "data": response})

    return StreamingResponse(analysis_generator(), media_type="text/event-stream")


# 서버 실행
if __name__ == "__main__":
    print("[START] GradioNaverSentiment API Server Starting...")
    print("[INFO] Swagger UI: http://localhost:8001/docs")
    print("[INFO] Frontend: http://localhost:5173 (Vite)")
    uvicorn.run(app, host="0.0.0.0", port=8001)
