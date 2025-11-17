// TypeScript 타입 정의

export interface SatisfactionCounts {
  '매우 불만족': number;
  '불만족': number;
  '보통': number;
  '만족': number;
  '매우 만족': number;
}

export interface SeasonalData {
  봄: { pos: number; neg: number };
  여름: { pos: number; neg: number };
  가을: { pos: number; neg: number };
  겨울: { pos: number; neg: number };
  정보없음: { pos: number; neg: number };
}

export interface TrendMetrics {
  trend_index: number;
  after_trend_index: number;
  before_avg: number;
  during_avg: number;
  after_avg: number;
}

export interface Judgment {
  sentence: string;
  final_verdict: string;
  score: number;
  satisfaction_level: number;
}

export interface BlogResult {
  '블로그 제목': string;
  '링크': string;
  '감성 빈도': number;
  '감성 점수': string;
  '긍정 문장 수': number;
  '부정 문장 수': number;
  '긍정 비율 (%)': string;
  '부정 비율 (%)': string;
  '긍/부정 문장 요약': string;
  '평균 만족도'?: string;
  judgments: Judgment[];
}

export interface KeywordAnalysisResponse {
  status: string;
  keyword: string;
  total_pos: number;
  total_neg: number;
  avg_satisfaction: number;
  satisfaction_counts: SatisfactionCounts;
  distribution_interpretation: string;
  all_scores: number[];
  outliers: number[];
  seasonal_data: SeasonalData;
  blog_results: BlogResult[];
  negative_summary: string;
  overall_summary: string;
  trend_metrics: TrendMetrics;
  url_markdown: string;
  focused_trend_graph?: string;
  trend_graph?: string;
  seasonal_word_clouds?: {
    봄?: { positive?: string; negative?: string };
    여름?: { positive?: string; negative?: string };
    가을?: { positive?: string; negative?: string };
    겨울?: { positive?: string; negative?: string };
  };
  // 상세 정보 테이블용 데이터
  addr1: string;
  addr2: string;
  areaCode: string | number;
  eventStartDate: string;
  eventEndDate: string;
  eventPeriod: number | string;
  sentiment_score: number;
  satisfaction_delta: number;
  emotion_keyword_freq: any;
}

export interface CategoryAnalysisResponse {
  status: string;
  category: string;
  total_festivals: number;
  analyzed_festivals: number;
  individual_results: any[];
  seasonal_data: SeasonalData;
  
  // Comprehensive analysis fields
  total_pos: number;
  total_neg: number;
  avg_satisfaction: number;
  satisfaction_counts: SatisfactionCounts;
  distribution_interpretation: string;
  all_scores: number[];
  outliers: number[];
  seasonal_word_clouds?: {
    봄?: { positive?: string; negative?: string };
    여름?: { positive?: string; negative?: string };
    가을?: { positive?: string; negative?: string };
    겨울?: { positive?: string; negative?: string };
  };
  category_overall_summary: string;
  category_negative_summary: string;
  trend_graph?: string;
  focused_trend_graph?: string;
}

export interface SeasonalFestival {
  순위: number;
  축제명: string;
  '최대 검색량': number;
  '평균 검색량': number;
  '행사 시작일': string;
  '행사 종료일': string;
  cat1: string;
  cat2: string;
  cat3: string;
}

export interface SeasonalTrendsResponse {
  status: string;
  season: string;
  wordcloud_url: string;
  timeline_url: string;
  top_festivals: SeasonalFestival[];
  festival_names: string[];
}

export interface ComparisonResponse {
  status: string;
  keyword_a: string;
  keyword_b: string;
  results_a: any;
  results_b: any;
  comparison_summary: string;
}

export interface CategoryComparisonResponse {
  status: string;
  category_a: string;
  category_b: string;
  results_a: {
    total_festivals: number;
    analyzed_festivals: number;
    total_pos: number;
    total_neg: number;
    avg_satisfaction: number;
    satisfaction_counts: SatisfactionCounts;
    seasonal_data: SeasonalData;
    category_overall_summary: string;
    distribution_interpretation: string;
  };
  results_b: {
    total_festivals: number;
    analyzed_festivals: number;
    total_pos: number;
    total_neg: number;
    avg_satisfaction: number;
    satisfaction_counts: SatisfactionCounts;
    seasonal_data: SeasonalData;
    category_overall_summary: string;
    distribution_interpretation: string;
  };
  comparison_summary: string;
}

export interface Festival {
  name: string;
  cat1: string;
  cat2: string;
  cat3: string;
}

// AI 추천 분석 관련 타입
export interface RecommendationResponse {
  status: string;
  keyword?: string;
  category?: string;
  keyword_a?: string;
  keyword_b?: string;
  category_a?: string;
  category_b?: string;
  region: string;
  season: string;
  recommendation: string;
}
