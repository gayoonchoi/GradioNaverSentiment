import axios from 'axios';
import type {
  KeywordAnalysisResponse,
  CategoryAnalysisResponse,
  ComparisonResponse,
} from '../types';

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

export default api;
