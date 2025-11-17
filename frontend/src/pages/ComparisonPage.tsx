import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  analyzeComparison,
  analyzeCategoryComparison,
  getCategories,
  getMediumCategories,
  getSmallCategories,
  getRecommendationForComparison,
  getRecommendationForCategoryComparison
} from '../lib/api'
import DonutChart from '../components/charts/DonutChart'
import SatisfactionChart from '../components/charts/SatisfactionChart'
import { FaSpinner, FaBalanceScale } from 'react-icons/fa'
import ReactMarkdown from 'react-markdown'

export default function ComparisonPage() {
  const [activeTab, setActiveTab] = useState<'festival' | 'category'>('festival')

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
  )
}

// 단일 축제 비교 컴포넌트
function FestivalComparison() {
  const [keywordA, setKeywordA] = useState('')
  const [keywordB, setKeywordB] = useState('')
  const [numReviews, setNumReviews] = useState(10)
  const [startAnalysis, setStartAnalysis] = useState(false)

  // AI 추천 분석 상태
  const [region, setRegion] = useState('')
  const [season, setSeason] = useState('')
  const [enableRecommendation, setEnableRecommendation] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['comparison', keywordA, keywordB, numReviews],
    queryFn: () => analyzeComparison(keywordA, keywordB, numReviews),
    enabled: startAnalysis && !!keywordA && !!keywordB,
    refetchOnMount: true,
  })

  const { data: recommendationData, isLoading: isRecommendationLoading, error: recommendationError } = useQuery({
    queryKey: ['comparison-recommendation', keywordA, keywordB, numReviews, region, season],
    queryFn: () => getRecommendationForComparison(keywordA, keywordB, numReviews, region, season),
    enabled: enableRecommendation && !!keywordA && !!keywordB && !!region && !!season,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!keywordA.trim() || !keywordB.trim()) {
      alert('두 축제명을 모두 입력해주세요')
      return
    }
    setStartAnalysis(true)
  }

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
            className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
          >
            비교 분석 시작
          </button>
        </form>
      </div>

      {/* 로딩 */}
      {isLoading && (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <FaSpinner className="animate-spin text-6xl text-primary mx-auto mb-4" />
            <p className="text-xl text-gray-600">
              {keywordA} vs {keywordB} 비교 분석 중...
            </p>
          </div>
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-800 mb-2">분석 실패</h2>
          <p className="text-red-600">{(error as Error).message}</p>
        </div>
      )}

      {/* 결과 */}
      {data && (
        <div className="space-y-8">
          {/* VS 헤더 */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl shadow-xl p-8 text-white">
            <div className="flex items-center justify-center space-x-8">
              <h2 className="text-3xl font-bold">{data.keyword_a}</h2>
              <FaBalanceScale className="text-5xl" />
              <h2 className="text-3xl font-bold">{data.keyword_b}</h2>
            </div>
          </div>

          {/* 비교 요약 */}
          {data.comparison_summary && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-2xl font-bold mb-4">AI 비교 분석</h3>
              <div className="prose max-w-none">
                <ReactMarkdown>{data.comparison_summary}</ReactMarkdown>
              </div>
            </div>
          )}

          {/* 나란히 비교 */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* 축제 A */}
            <div className="bg-blue-50 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-blue-900 mb-4">
                {data.keyword_a}
              </h3>
              {data.results_a && (
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4">
                    <h4 className="font-bold mb-2">긍정/부정 비율</h4>
                    <DonutChart
                      positive={data.results_a.total_pos || 0}
                      negative={data.results_a.total_neg || 0}
                    />
                  </div>
                  {data.results_a.satisfaction_counts && (
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="font-bold mb-2">만족도 분포</h4>
                      <SatisfactionChart
                        counts={data.results_a.satisfaction_counts}
                      />
                    </div>
                  )}
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-sm text-gray-600">평균 만족도</div>
                    <div className="text-3xl font-bold text-green-600">
                      {data.results_a.avg_satisfaction?.toFixed(2) || 'N/A'} / 5.0
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 축제 B */}
            <div className="bg-purple-50 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-purple-900 mb-4">
                {data.keyword_b}
              </h3>
              {data.results_b && (
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4">
                    <h4 className="font-bold mb-2">긍정/부정 비율</h4>
                    <DonutChart
                      positive={data.results_b.total_pos || 0}
                      negative={data.results_b.total_neg || 0}
                    />
                  </div>
                  {data.results_b.satisfaction_counts && (
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="font-bold mb-2">만족도 분포</h4>
                      <SatisfactionChart
                        counts={data.results_b.satisfaction_counts}
                      />
                    </div>
                  )}
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-sm text-gray-600">평균 만족도</div>
                    <div className="text-3xl font-bold text-green-600">
                      {data.results_b.avg_satisfaction?.toFixed(2) || 'N/A'} / 5.0
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* AI 비교 추천 분석 */}
      {data && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">🤖 AI 비교 추천 분석</h2>
          <p className="text-gray-600 mb-6">
            지역과 계절을 입력하면 AI가 두 축제를 비교하여 해당 조건에서 어느 축제가 더 적합한지 추천해드립니다.
          </p>

          {/* 입력 폼 */}
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

          {/* 추천 결과 표시 */}
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
  )
}

// 카테고리 비교 컴포넌트
function CategoryComparison() {
  // 카테고리 A
  const [cat1A, setCat1A] = useState('')
  const [cat2A, setCat2A] = useState('')
  const [cat3A, setCat3A] = useState('')

  // 카테고리 B
  const [cat1B, setCat1B] = useState('')
  const [cat2B, setCat2B] = useState('')
  const [cat3B, setCat3B] = useState('')

  const [numReviews, setNumReviews] = useState(10)
  const [startAnalysis, setStartAnalysis] = useState(false)

  // AI 추천 분석 상태
  const [region, setRegion] = useState('')
  const [season, setSeason] = useState('')
  const [enableRecommendation, setEnableRecommendation] = useState(false)

  // 카테고리 데이터 로드
  const { data: cat1List } = useQuery({ queryKey: ['categories'], queryFn: getCategories })
  const { data: cat2AList } = useQuery({ queryKey: ['medium-categories', cat1A], queryFn: () => getMediumCategories(cat1A), enabled: !!cat1A })
  const { data: cat3AList } = useQuery({ queryKey: ['small-categories', cat1A, cat2A], queryFn: () => getSmallCategories(cat1A, cat2A), enabled: !!cat1A && !!cat2A })
  const { data: cat2BList } = useQuery({ queryKey: ['medium-categories', cat1B], queryFn: () => getMediumCategories(cat1B), enabled: !!cat1B })
  const { data: cat3BList } = useQuery({ queryKey: ['small-categories', cat1B, cat2B], queryFn: () => getSmallCategories(cat1B, cat2B), enabled: !!cat1B && !!cat2B })

  const { data, isLoading, error } = useQuery({
    queryKey: ['category-comparison', cat1A, cat2A, cat3A, cat1B, cat2B, cat3B, numReviews],
    queryFn: () => analyzeCategoryComparison(cat1A, cat2A, cat3A, cat1B, cat2B, cat3B, numReviews),
    enabled: startAnalysis && !!cat1A && !!cat2A && !!cat3A && !!cat1B && !!cat2B && !!cat3B,
    refetchOnMount: true,
  })

  const { data: recommendationData, isLoading: isRecommendationLoading, error: recommendationError } = useQuery({
    queryKey: ['category-comparison-recommendation', cat1A, cat2A, cat3A, cat1B, cat2B, cat3B, numReviews, region, season],
    queryFn: () => getRecommendationForCategoryComparison(cat1A, cat2A, cat3A, cat1B, cat2B, cat3B, numReviews, region, season),
    enabled: enableRecommendation && !!cat1A && !!cat2A && !!cat3A && !!cat1B && !!cat2B && !!cat3B && !!region && !!season,
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!cat1A || !cat2A || !cat3A || !cat1B || !cat2B || !cat3B) {
      alert('두 카테고리를 모두 선택해주세요')
      return
    }
    setStartAnalysis(true)
  }

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
            className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
          >
            카테고리 비교 분석 시작
          </button>
        </form>
      </div>

      {/* 로딩 */}
      {isLoading && (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <FaSpinner className="animate-spin text-6xl text-primary mx-auto mb-4" />
            <p className="text-xl text-gray-600">
              카테고리 비교 분석 중...
              <br />
              <span className="text-sm">
                {cat1A} &gt; {cat2A} &gt; {cat3A} vs {cat1B} &gt; {cat2B} &gt; {cat3B}
                <br />
                여러 축제를 동시에 분석합니다 (5-15분 소요 가능)
              </span>
            </p>
          </div>
        </div>
      )}

      {/* 에러 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-bold text-red-800 mb-2">분석 실패</h2>
          <p className="text-red-600">{(error as Error).message}</p>
        </div>
      )}

      {/* 결과 */}
      {data && (
        <div className="space-y-8">
          {/* VS 헤더 */}
          <div className="bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl shadow-xl p-8 text-white">
            <div className="flex items-center justify-center space-x-8">
              <h2 className="text-2xl font-bold text-center">{data.category_a}</h2>
              <FaBalanceScale className="text-5xl" />
              <h2 className="text-2xl font-bold text-center">{data.category_b}</h2>
            </div>
          </div>

          {/* 비교 요약 */}
          {data.comparison_summary && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h3 className="text-2xl font-bold mb-4">AI 비교 분석</h3>
              <div className="prose max-w-none">
                <ReactMarkdown>{data.comparison_summary}</ReactMarkdown>
              </div>
            </div>
          )}

          {/* 나란히 비교 */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* 카테고리 A */}
            <div className="bg-blue-50 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-blue-900 mb-4">
                {data.category_a}
              </h3>
              {data.results_a && (
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">전체 축제:</span>
                        <span className="font-bold ml-2">{data.results_a.total_festivals}개</span>
                      </div>
                      <div>
                        <span className="text-gray-600">분석 완료:</span>
                        <span className="font-bold ml-2">{data.results_a.analyzed_festivals}개</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <h4 className="font-bold mb-2">긍정/부정 비율</h4>
                    <DonutChart
                      positive={data.results_a.total_pos || 0}
                      negative={data.results_a.total_neg || 0}
                    />
                  </div>
                  {data.results_a.satisfaction_counts && (
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="font-bold mb-2">만족도 분포</h4>
                      <SatisfactionChart
                        counts={data.results_a.satisfaction_counts}
                      />
                    </div>
                  )}
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-sm text-gray-600">평균 만족도</div>
                    <div className="text-3xl font-bold text-green-600">
                      {data.results_a.avg_satisfaction?.toFixed(2) || 'N/A'} / 5.0
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* 카테고리 B */}
            <div className="bg-purple-50 rounded-xl p-6">
              <h3 className="text-2xl font-bold text-purple-900 mb-4">
                {data.category_b}
              </h3>
              {data.results_b && (
                <div className="space-y-4">
                  <div className="bg-white rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-gray-600">전체 축제:</span>
                        <span className="font-bold ml-2">{data.results_b.total_festivals}개</span>
                      </div>
                      <div>
                        <span className="text-gray-600">분석 완료:</span>
                        <span className="font-bold ml-2">{data.results_b.analyzed_festivals}개</span>
                      </div>
                    </div>
                  </div>
                  <div className="bg-white rounded-lg p-4">
                    <h4 className="font-bold mb-2">긍정/부정 비율</h4>
                    <DonutChart
                      positive={data.results_b.total_pos || 0}
                      negative={data.results_b.total_neg || 0}
                    />
                  </div>
                  {data.results_b.satisfaction_counts && (
                    <div className="bg-white rounded-lg p-4">
                      <h4 className="font-bold mb-2">만족도 분포</h4>
                      <SatisfactionChart
                        counts={data.results_b.satisfaction_counts}
                      />
                    </div>
                  )}
                  <div className="bg-white rounded-lg p-4">
                    <div className="text-sm text-gray-600">평균 만족도</div>
                    <div className="text-3xl font-bold text-green-600">
                      {data.results_b.avg_satisfaction?.toFixed(2) || 'N/A'} / 5.0
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* AI 비교 추천 분석 */}
      {data && (
        <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">🤖 AI 비교 추천 분석</h2>
          <p className="text-gray-600 mb-6">
            지역과 계절을 입력하면 AI가 두 카테고리를 비교하여 해당 조건에서 어느 카테고리가 더 적합한지 추천해드립니다.
          </p>

          {/* 입력 폼 */}
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

          {/* 추천 결과 표시 */}
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
  )
}
