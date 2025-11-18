import { useState, FC } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  analyzeComparisonStream,
  analyzeCategoryComparisonStream,
  getCategories,
  getMediumCategories,
  getSmallCategories,
  getRecommendationForComparison,
  getRecommendationForCategoryComparison,
  ProgressEvent,
} from '../lib/api';
import { ComparisonResponse, CategoryComparisonResponse, KeywordAnalysisResponse, CategoryAnalysisResponse } from '../types';
import DonutChart from '../components/charts/DonutChart';
import SatisfactionChart from '../components/charts/SatisfactionChart';
import AbsoluteScoreChart from '../components/charts/AbsoluteScoreChart';
import OutlierChart from '../components/charts/OutlierChart';
import SeasonalTabs from '../components/seasonal/SeasonalTabs';
import BlogTable from '../components/BlogTable';
import { FaBalanceScale } from 'react-icons/fa';
import ReactMarkdown from 'react-markdown';
import { SERVER_URL } from '../lib/api';

// 로딩 컴포넌트
function AnalysisProgress({ progress, title }: { progress: ProgressEvent; title: string }) {
  const percent = Math.round(progress.percent * 100);
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center w-full max-w-2xl p-8">
        <h2 className="text-2xl font-bold text-primary mb-4">{title}</h2>
        <div className="w-full bg-gray-200 rounded-full h-4 mb-4 overflow-hidden">
          <div
            className="bg-primary h-4 rounded-full transition-all duration-300 ease-in-out"
            style={{ width: `${percent}%` }}
          ></div>
        </div>
        <p className="text-xl font-semibold text-gray-700 mb-2">{percent}%</p>
        <p className="text-md text-gray-500 whitespace-pre-wrap">{progress.message}</p>
      </div>
    </div>
  );
}

const Section: FC<{ title: string; children: React.ReactNode; className?: string }> = ({ title, children, className = '' }) => (
  <div className={`bg-white rounded-xl shadow-md p-6 ${className}`}>
    <h3 className="text-xl font-bold text-gray-800 mb-4">{title}</h3>
    {children}
  </div>
);

// 단일 키워드 분석 결과 상세 뷰
const KeywordAnalysisDetails: FC<{ result: KeywordAnalysisResponse }> = ({ result }) => {
  return (
    <div className="space-y-6">
      <Section title="총합 평가">
        <div className="prose max-w-none">
          <ReactMarkdown>{result.overall_summary}</ReactMarkdown>
        </div>
      </Section>
      <Section title="AI 분석 해석">
        <div className="prose max-w-none">
          <ReactMarkdown>{result.distribution_interpretation}</ReactMarkdown>
        </div>
      </Section>
      <Section title="주요 불만 사항">
        <div className="prose max-w-none">
          <ReactMarkdown>{result.negative_summary}</ReactMarkdown>
        </div>
      </Section>
      <Section title="전체 긍정/부정 비율">
        <DonutChart positive={result.total_pos} negative={result.total_neg} />
      </Section>
      <Section title="만족도 5단계 분포">
        <SatisfactionChart counts={result.satisfaction_counts} />
      </Section>
      <Section title="절대 점수 분포">
        <AbsoluteScoreChart scores={result.all_scores} />
      </Section>
      <Section title="이상치 분석 (BoxPlot)">
        <OutlierChart scores={result.all_scores} />
      </Section>
      <Section title="트렌드 분석 - 집중 트렌드 (축제 기간 중심)">
        {result.focused_trend_graph && <img src={`${SERVER_URL}${result.focused_trend_graph}`} alt="집중 트렌드" className="w-full h-auto" />}
      </Section>
      <Section title="트렌드 분석 - 전체 트렌드 (1년)">
        {result.trend_graph && <img src={`${SERVER_URL}${result.trend_graph}`} alt="전체 트렌드" className="w-full h-auto" />}
      </Section>
      <Section title="계절별 분석">
        <SeasonalTabs seasonalData={result.seasonal_data} seasonalWordClouds={result.seasonal_word_clouds} />
      </Section>
      <Section title="블로그 분석 결과">
        <BlogTable blogs={result.blog_results} />
      </Section>
    </div>
  );
};

// 카테고리 분석 결과 상세 뷰
const CategoryAnalysisDetails: FC<{ result: CategoryAnalysisResponse }> = ({ result }) => {
  return (
    <div className="space-y-6">
      <Section title="총합 평가">
        <div className="prose max-w-none">
          <ReactMarkdown>{result.category_overall_summary}</ReactMarkdown>
        </div>
      </Section>
      <Section title="AI 분석 해석">
        <div className="prose max-w-none">
          <ReactMarkdown>{result.distribution_interpretation}</ReactMarkdown>
        </div>
      </Section>
      <Section title="주요 불만 사항">
        <div className="prose max-w-none">
          <ReactMarkdown>{result.category_negative_summary}</ReactMarkdown>
        </div>
      </Section>
      <Section title="전체 긍정/부정 비율">
        <DonutChart positive={result.total_pos} negative={result.total_neg} />
      </Section>
      <Section title="만족도 5단계 분포">
        <SatisfactionChart counts={result.satisfaction_counts} />
      </Section>
      <Section title="절대 점수 분포">
        <AbsoluteScoreChart scores={result.all_scores} />
      </Section>
      <Section title="이상치 분석 (BoxPlot)">
        <OutlierChart scores={result.all_scores} />
      </Section>
      <Section title="계절별 분석">
        <SeasonalTabs seasonalData={result.seasonal_data} seasonalWordClouds={result.seasonal_word_clouds} />
      </Section>
       <Section title="키워드 워드클라우드">
        {result.keyword_wordclouds && Object.entries(result.keyword_wordclouds).map(([keyword, url]) =>
          url ? <img key={keyword} src={`${SERVER_URL}${url}`} alt={`${keyword} 워드클라우드`} className="w-full h-auto mb-4" /> : null
        )}
      </Section>
    </div>
  );
};


export default function ComparisonPage() {
  const [activeTab, setActiveTab] = useState<'festival' | 'category'>('festival');

  return (
    <div className="space-y-8">
      {/* 탭 헤더 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">비교 분석</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('festival')}
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              activeTab === 'festival'
                ? 'bg-primary text-white shadow-lg'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            단일 축제 비교
          </button>
          <button
            onClick={() => setActiveTab('category')}
            className={`px-6 py-3 rounded-lg font-semibold transition ${
              activeTab === 'category'
                ? 'bg-primary text-white shadow-lg'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            카테고리 비교
          </button>
        </div>
      </div>

      {/* 탭 컨텐츠 */}
      {activeTab === 'festival' ? <FestivalComparison /> : <CategoryComparison />}
    </div>
  );
}

// 단일 축제 비교 컴포넌트
function FestivalComparison() {
  const [keywordA, setKeywordA] = useState('');
  const [keywordB, setKeywordB] = useState('');
  const [numReviews, setNumReviews] = useState(10);

  // Analysis state
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressEvent>({ percent: 0, message: '대기 중...' });

  // AI 추천 분석 상태
  const [region, setRegion] = useState('');
  const [season, setSeason] = useState('');
  const [enableRecommendation, setEnableRecommendation] = useState(false);

  const { data: recommendationData, isLoading: isRecommendationLoading, error: recommendationError } = useQuery({
    queryKey: ['comparison-recommendation', keywordA, keywordB, numReviews, region, season],
    queryFn: () => getRecommendationForComparison(keywordA, keywordB, numReviews, region, season),
    enabled: enableRecommendation && !!keywordA && !!keywordB && !!region && !!season,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!keywordA.trim() || !keywordB.trim()) {
      alert('두 축제명을 모두 입력해주세요');
      return;
    }
    setIsLoading(true);
    setData(null);
    setError(null);
    setProgress({ percent: 0, message: '비교 분석 시작...' });

    analyzeComparisonStream(
      keywordA, keywordB, numReviews,
      (p) => setProgress(p),
      (res) => {
        setData(res);
        setIsLoading(false);
      },
      (err) => {
        setError(err);
        setIsLoading(false);
      }
    );
  };

  return (
    <>
      {/* 입력 폼 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">축제 직접 입력</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                축제 A
              </label>
              <input
                type="text"
                value={keywordA}
                onChange={(e) => setKeywordA(e.target.value)}
                placeholder="예: 강릉커피축제"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                축제 B
              </label>
              <input
                type="text"
                value={keywordB}
                onChange={(e) => setKeywordB(e.target.value)}
                placeholder="예: 보령머드축제"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
              />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              분석할 리뷰 수: {numReviews}개
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={numReviews}
              onChange={(e) => setNumReviews(Number(e.target.value))}
              className="w-full"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition disabled:bg-gray-400"
          >
            {isLoading ? '분석 중...' : '비교 분석 시작'}
          </button>
        </form>
      </div>

      {isLoading && <AnalysisProgress progress={progress} title={`${keywordA} vs ${keywordB}`} />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-800 mb-2">분석 실패</h2>
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {data && (
        <div className="space-y-8">
          <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl shadow-xl p-8 text-white">
            <div className="flex items-center justify-center space-x-8">
              <h2 className="text-3xl font-bold">{data.keyword_a}</h2>
              <FaBalanceScale className="text-5xl" />
              <h2 className="text-3xl font-bold">{data.keyword_b}</h2>
            </div>
          </div>

          {data.comparison_summary && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-2xl font-bold mb-4">AI 비교 분석 요약</h3>
              <div className="prose max-w-none">
                <ReactMarkdown>{data.comparison_summary}</ReactMarkdown>
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-blue-50 rounded-xl p-6 space-y-6">
              <h3 className="text-2xl font-bold text-blue-900 mb-4">
                {data.keyword_a} 상세 분석
              </h3>
              {data.results_a && <KeywordAnalysisDetails result={data.results_a} />}
            </div>

            <div className="bg-purple-50 rounded-xl p-6 space-y-6">
              <h3 className="text-2xl font-bold text-purple-900 mb-4">
                {data.keyword_b} 상세 분석
              </h3>
              {data.results_b && <KeywordAnalysisDetails result={data.results_b} />}
            </div>
          </div>
        </div>
      )}

      {data && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">🤖 AI 비교 추천 분석</h2>
          <p className="text-gray-600 mb-6">
            지역과 계절을 입력하면 AI가 두 축제를 비교하여 해당 조건에서 어느 축제가 더 적합한지 추천해드립니다.
          </p>
          <div className="bg-white rounded-lg p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  지역 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="예: 서울, 부산, 제주"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  계절 <span className="text-red-500">*</span>
                </label>
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">선택하세요</option>
                  <option value="봄">봄</option>
                  <option value="여름">여름</option>
                  <option value="가을">가을</option>
                  <option value="겨울">겨울</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => setEnableRecommendation(true)}
                  disabled={!region || !season || isRecommendationLoading}
                  className="w-full px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition"
                >
                  {isRecommendationLoading ? 'AI 분석 중...' : 'AI 비교 추천 시작'}
                </button>
              </div>
            </div>
          </div>
          {isRecommendationLoading && (
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <p className="text-gray-600">AI가 비교 분석 중입니다...</p>
            </div>
          )}
          {recommendationError && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
              <p className="text-red-700">
                추천 분석 중 오류가 발생했습니다: {(recommendationError as Error).message}
              </p>
            </div>
          )}
          {recommendationData && !isRecommendationLoading && (
            <div className="bg-white rounded-lg p-6">
              <div className="mb-4 flex items-center space-x-2 text-sm text-gray-600">
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-semibold">
                  {recommendationData.region}
                </span>
                <span className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full font-semibold">
                  {recommendationData.season}
                </span>
              </div>
              <div className="prose prose-lg max-w-none">
                <ReactMarkdown>{recommendationData.recommendation}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}

// 카테고리 비교 컴포넌트
function CategoryComparison() {
  // 카테고리 A
  const [cat1A, setCat1A] = useState('');
  const [cat2A, setCat2A] = useState('');
  const [cat3A, setCat3A] = useState('');

  // 카테고리 B
  const [cat1B, setCat1B] = useState('');
  const [cat2B, setCat2B] = useState('');
  const [cat3B, setCat3B] = useState('');

  const [numReviews, setNumReviews] = useState(10);
  
  // Analysis state
  const [data, setData] = useState<CategoryComparisonResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressEvent>({ percent: 0, message: '대기 중...' });

  // AI 추천 분석 상태
  const [region, setRegion] = useState('');
  const [season, setSeason] = useState('');
  const [enableRecommendation, setEnableRecommendation] = useState(false);

  // 카테고리 데이터 로드
  const { data: cat1List } = useQuery({ queryKey: ['categories'], queryFn: getCategories });
  const { data: cat2AList } = useQuery({ queryKey: ['medium-categories', cat1A], queryFn: () => getMediumCategories(cat1A), enabled: !!cat1A });
  const { data: cat3AList } = useQuery({ queryKey: ['small-categories', cat1A, cat2A], queryFn: () => getSmallCategories(cat1A, cat2A), enabled: !!cat1A && !!cat2A });
  const { data: cat2BList } = useQuery({ queryKey: ['medium-categories', cat1B], queryFn: () => getMediumCategories(cat1B), enabled: !!cat1B });
  const { data: cat3BList } = useQuery({ queryKey: ['small-categories', cat1B, cat2B], queryFn: () => getSmallCategories(cat1B, cat2B), enabled: !!cat1B && !!cat2B });

  const { data: recommendationData, isLoading: isRecommendationLoading, error: recommendationError } = useQuery({
    queryKey: ['category-comparison-recommendation', cat1A, cat2A, cat3A, cat1B, cat2B, cat3B, numReviews, region, season],
    queryFn: () => getRecommendationForCategoryComparison(cat1A, cat2A, cat3A, cat1B, cat2B, cat3B, numReviews, region, season),
    enabled: enableRecommendation && !!cat1A && !!cat2A && !!cat3A && !!cat1B && !!cat2B && !!cat3B && !!region && !!season,
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cat1A || !cat2A || !cat3A || !cat1B || !cat2B || !cat3B) {
      alert('두 카테고리를 모두 선택해주세요');
      return;
    }
    setIsLoading(true);
    setData(null);
    setError(null);
    setProgress({ percent: 0, message: '카테고리 비교 분석 시작...' });

    analyzeCategoryComparisonStream(
      cat1A, cat2A, cat3A,
      cat1B, cat2B, cat3B,
      numReviews,
      (p) => setProgress(p),
      (res) => {
        setData(res);
        setIsLoading(false);
      },
      (err) => {
        setError(err);
        setIsLoading(false);
      }
    );
  };

  return (
    <>
      {/* 입력 폼 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">카테고리 선택</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid md:grid-cols-2 gap-8">
            {/* 카테고리 A */}
            <div className="bg-blue-50 rounded-lg p-4">
              <h3 className="text-lg font-bold text-blue-900 mb-3">카테고리 A</h3>
              <div className="space-y-3">
                <select
                  value={cat1A}
                  onChange={(e) => { setCat1A(e.target.value); setCat2A(''); setCat3A(''); }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">대분류 선택</option>
                  {cat1List?.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={cat2A}
                  onChange={(e) => { setCat2A(e.target.value); setCat3A(''); }}
                  disabled={!cat1A}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                >
                  <option value="">중분류 선택</option>
                  {cat2AList?.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={cat3A}
                  onChange={(e) => setCat3A(e.target.value)}
                  disabled={!cat2A}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
                >
                  <option value="">소분류 선택</option>
                  {cat3AList?.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* 카테고리 B */}
            <div className="bg-purple-50 rounded-lg p-4">
              <h3 className="text-lg font-bold text-purple-900 mb-3">카테고리 B</h3>
              <div className="space-y-3">
                <select
                  value={cat1B}
                  onChange={(e) => { setCat1B(e.target.value); setCat2B(''); setCat3B(''); }}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                >
                  <option value="">대분류 선택</option>
                  {cat1List?.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={cat2B}
                  onChange={(e) => { setCat2B(e.target.value); setCat3B(''); }}
                  disabled={!cat1B}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100"
                >
                  <option value="">중분류 선택</option>
                  {cat2BList?.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <select
                  value={cat3B}
                  onChange={(e) => setCat3B(e.target.value)}
                  disabled={!cat2B}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100"
                >
                  <option value="">소분류 선택</option>
                  {cat3BList?.map((cat) => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              분석할 리뷰 수: {numReviews}개 (각 축제당)
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={numReviews}
              onChange={(e) => setNumReviews(Number(e.target.value))}
              className="w-full"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition disabled:bg-gray-400"
          >
            {isLoading ? '분석 중...' : '카테고리 비교 분석 시작'}
          </button>
        </form>
      </div>

      {isLoading && <AnalysisProgress progress={progress} title={`${cat3A} vs ${cat3B}`} />}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-800 mb-2">분석 실패</h2>
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {data && (
        <div className="space-y-8">
          <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl shadow-xl p-8 text-white">
            <div className="flex items-center justify-center space-x-8">
              <h2 className="text-2xl font-bold text-center">{data.category_a}</h2>
              <FaBalanceScale className="text-5xl" />
              <h2 className="text-2xl font-bold text-center">{data.category_b}</h2>
            </div>
          </div>

          {data.comparison_summary && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-2xl font-bold mb-4">AI 비교 분석 요약</h3>
              <div className="prose max-w-none">
                <ReactMarkdown>{data.comparison_summary}</ReactMarkdown>
              </div>
            </div>
          )}

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-blue-50 rounded-xl p-6 space-y-6">
              <h3 className="text-2xl font-bold text-blue-900 mb-4">
                {data.category_a} 상세 분석
              </h3>
              {data.results_a && <CategoryAnalysisDetails result={data.results_a} />}
            </div>

            <div className="bg-purple-50 rounded-xl p-6 space-y-6">
              <h3 className="text-2xl font-bold text-purple-900 mb-4">
                {data.category_b} 상세 분석
              </h3>
              {data.results_b && <CategoryAnalysisDetails result={data.results_b} />}
            </div>
          </div>
        </div>
      )}

      {data && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">🤖 AI 비교 추천 분석</h2>
          <p className="text-gray-600 mb-6">
            지역과 계절을 입력하면 AI가 두 카테고리를 비교하여 해당 조건에서 어느 카테고리가 더 적합한지 추천해드립니다.
          </p>
          <div className="bg-white rounded-lg p-6 mb-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  지역 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  placeholder="예: 서울, 부산, 제주"
                  value={region}
                  onChange={(e) => setRegion(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  계절 <span className="text-red-500">*</span>
                </label>
                <select
                  value={season}
                  onChange={(e) => setSeason(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                >
                  <option value="">선택하세요</option>
                  <option value="봄">봄</option>
                  <option value="여름">여름</option>
                  <option value="가을">가을</option>
                  <option value="겨울">겨울</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={() => setEnableRecommendation(true)}
                  disabled={!region || !season || isRecommendationLoading}
                  className="w-full px-6 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed transition"
                >
                  {isRecommendationLoading ? 'AI 분석 중...' : 'AI 비교 추천 시작'}
                </button>
              </div>
            </div>
          </div>
          {isRecommendationLoading && (
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
              <p className="text-gray-600">AI가 비교 분석 중입니다...</p>
            </div>
          )}
          {recommendationError && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded">
              <p className="text-red-700">
                추천 분석 중 오류가 발생했습니다: {(recommendationError as Error).message}
              </p>
            </div>
          )}
          {recommendationData && !isRecommendationLoading && (
            <div className="bg-white rounded-lg p-6">
              <div className="mb-4 flex items-center space-x-2 text-sm text-gray-600">
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-semibold">
                  {recommendationData.region}
                </span>
                <span className="px-3 py-1 bg-pink-100 text-pink-700 rounded-full font-semibold">
                  {recommendationData.season}
                </span>
              </div>
              <div className="prose prose-lg max-w-none">
                <ReactMarkdown>{recommendationData.recommendation}</ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      )}
    </>
  );
}
