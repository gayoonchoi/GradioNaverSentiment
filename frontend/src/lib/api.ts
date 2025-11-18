import axios from 'axios';
import type {
  KeywordAnalysisResponse,
  CategoryAnalysisResponse,
  ComparisonResponse,
  CategoryComparisonResponse,
  SeasonalTrendsResponse,
  RecommendationResponse,
} from '../types';

export const SERVER_URL = 'http://localhost:8001';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 카테고리 설정 API
export const getCategories = async (): Promise<string[]> => {
  const { data } = await api.get('/config/categories');
  return data.categories;
};

export const getMediumCategories = async (cat1: string): Promise<string[]> => {
  const { data } = await api.get('/config/categories/medium', {
    params: { cat1 },
  });
  return data.categories;
};

export const getSmallCategories = async (
  cat1: string,
  cat2: string
): Promise<string[]> => {
  const { data } = await api.get('/config/categories/small', {
    params: { cat1, cat2 },
  });
  return data.categories;
};

export const getFestivals = async (
  cat1: string,
  cat2: string,
  cat3: string
): Promise<string[]> => {
  const { data } = await api.get('/config/festivals', {
    params: { cat1, cat2, cat3 },
  });
  return data.festivals;
};

// 감성 분석 API
export const analyzeKeyword = async (
  keyword: string,
  numReviews: number = 10,
  logDetails: boolean = true
): Promise<KeywordAnalysisResponse> => {
  const { data } = await api.post('/analyze/keyword', {
    keyword,
    num_reviews: numReviews,
    log_details: logDetails,
  });
  return data;
};

export const analyzeCategory = async (
  cat1: string,
  cat2: string,
  cat3: string,
  numReviews: number = 10
): Promise<CategoryAnalysisResponse> => {
  const { data } = await api.post('/analyze/category', {
    cat1,
    cat2,
    cat3,
    num_reviews: numReviews,
  });
  return data;
};

export const analyzeComparison = async (
  keywordA: string,
  keywordB: string,
  numReviews: number = 10
): Promise<ComparisonResponse> => {
  const { data } = await api.post('/analyze/comparison', {
    keyword_a: keywordA,
    keyword_b: keywordB,
    num_reviews: numReviews,
  });
  return data;
};

export const analyzeCategoryComparison = async (
  cat1A: string,
  cat2A: string,
  cat3A: string,
  cat1B: string,
  cat2B: string,
  cat3B: string,
  numReviews: number = 10
): Promise<CategoryComparisonResponse> => {
  const { data } = await api.post('/analyze/category-comparison', {
    cat1_a: cat1A,
    cat2_a: cat2A,
    cat3_a: cat3A,
    cat1_b: cat1B,
    cat2_b: cat2B,
    cat3_b: cat3B,
    num_reviews: numReviews,
  });
  return data;
};

// 계절별 트렌드 API
export interface FestivalTrendResponse {
  status: string;
  festival_name: string;
  trend_graph_url: string;
}

export const getSeasonalTrends = async (
  season: string
): Promise<SeasonalTrendsResponse> => {
  const { data } = await api.get('/seasonal/analyze', {
    params: { season },
  });
  return data;
};

export const getFestivalTrend = async (
  festivalName: string,
  season?: string
): Promise<FestivalTrendResponse> => {
  const { data } = await api.get('/seasonal/festival-trend', {
    params: { festival_name: festivalName, season },
  });
  return data;
};

// AI 추천 분석 API
export const getRecommendationForSingle = async (
  keyword: string,
  numReviews: number,
  region: string,
  season: string
): Promise<RecommendationResponse> => {
  const { data } = await api.post('/recommend/single', {
    keyword,
    num_reviews: numReviews,
    region,
    season,
  });
  return data;
};

export const getRecommendationForCategory = async (
  cat1: string,
  cat2: string,
  cat3: string,
  numReviews: number,
  region: string,
  season: string
): Promise<RecommendationResponse> => {
  const { data } = await api.post('/recommend/category', {
    cat1,
    cat2,
    cat3,
    num_reviews: numReviews,
    region,
    season,
  });
  return data;
};

export const getRecommendationForComparison = async (
  keywordA: string,
  keywordB: string,
  numReviews: number,
  region: string,
  season: string
): Promise<RecommendationResponse> => {
  const { data } = await api.post('/recommend/comparison', {
    keyword_a: keywordA,
    keyword_b: keywordB,
    num_reviews: numReviews,
    region,
    season,
  });
  return data;
};

export const getRecommendationForCategoryComparison = async (
  cat1A: string,
  cat2A: string,
  cat3A: string,
  cat1B: string,
  cat2B: string,
  cat3B: string,
  numReviews: number,
  region: string,
  season: string
): Promise<RecommendationResponse> => {
  const { data } = await api.post('/recommend/category-comparison', {
    cat1_a: cat1A,
    cat2_a: cat2A,
    cat3_a: cat3A,
    cat1_b: cat1B,
    cat2_b: cat2B,
    cat3_b: cat3B,
    num_reviews: numReviews,
    region,
    season,
  });
  return data;
};

export default api;

// ==================== Streaming API ====================

export interface ProgressEvent {
  percent: number;
  message: string;
}

type ProgressCallback = (progress: ProgressEvent) => void;
type ResultCallback<T> = (result: T) => void;
type ErrorCallback = (error: string) => void;

async function fetchStream<T>(
  url: string,
  body: any,
  onProgress: ProgressCallback,
  onResult: ResultCallback<T>,
  onError: ErrorCallback
) {
  try {
    const response = await fetch(`/api${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('Response body is not readable');
    }

    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    const processText = (text: string) => {
      buffer += text;
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep the last partial line

      for (const line of lines) {
        if (line.startsWith('data:')) {
          const jsonString = line.substring(5).trim();
          if (jsonString) {
            try {
              const parsed = JSON.parse(jsonString);
              if (parsed.type === 'progress') {
                onProgress(parsed);
              } else if (parsed.type === 'result') {
                onResult(parsed.data);
              } else if (parsed.type === 'error') {
                onError(parsed.message);
              }
            } catch (e) {
              console.error('Failed to parse SSE message:', jsonString, e);
              onError('데이터 파싱 중 오류가 발생했습니다.');
            }
          }
        }
      }
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        break;
      }
      processText(decoder.decode(value, { stream: true }));
    }
  } catch (err) {
    console.error('Streaming fetch failed:', err);
    onError((err as Error).message);
  }
}

export const analyzeKeywordStream = (
  keyword: string,
  numReviews: number,
  onProgress: ProgressCallback,
  onResult: ResultCallback<KeywordAnalysisResponse>,
  onError: ErrorCallback
) => {
  fetchStream(
    '/analyze/keyword/stream',
    { keyword, num_reviews: numReviews, log_details: true },
    onProgress,
    onResult,
    onError
  );
};

export const analyzeCategoryStream = (
  cat1: string,
  cat2: string,
  cat3: string,
  numReviews: number,
  onProgress: ProgressCallback,
  onResult: ResultCallback<CategoryAnalysisResponse>,
  onError: ErrorCallback
) => {
  fetchStream(
    '/analyze/category/stream',
    { cat1, cat2, cat3, num_reviews: numReviews },
    onProgress,
    onResult,
    onError
  );
};

export const analyzeComparisonStream = (
  keywordA: string,
  keywordB: string,
  numReviews: number,
  onProgress: ProgressCallback,
  onResult: ResultCallback<ComparisonResponse>,
  onError: ErrorCallback
) => {
  fetchStream(
    '/analyze/comparison/stream',
    { keyword_a: keywordA, keyword_b: keywordB, num_reviews: numReviews },
    onProgress,
    onResult,
    onError
  );
};

export const analyzeCategoryComparisonStream = (
  cat1A: string, cat2A: string, cat3A: string,
  cat1B: string, cat2B: string, cat3B: string,
  numReviews: number,
  onProgress: ProgressCallback,
  onResult: ResultCallback<CategoryComparisonResponse>,
  onError: ErrorCallback
) => {
  fetchStream(
    '/analyze/category-comparison/stream',
    { 
      cat1_a: cat1A, cat2_a: cat2A, cat3_a: cat3A,
      cat1_b: cat1B, cat2_b: cat2B, cat3_b: cat3B,
      num_reviews: numReviews 
    },
    onProgress,
    onResult,
    onError
  );
};
