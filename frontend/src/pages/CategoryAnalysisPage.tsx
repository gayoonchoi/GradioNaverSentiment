import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { analyzeCategory, getRecommendationForCategory } from '../lib/api'
import { useState } from 'react'
import DonutChart from '../components/charts/DonutChart'
import ReactMarkdown from 'react-markdown'
import ExplanationToggle from '../components/common/ExplanationToggle'
import { explanations } from '../lib/explanations'
import SeasonalTabs from '../components/seasonal/SeasonalTabs'
import SatisfactionChart from '../components/charts/SatisfactionChart'
import AbsoluteScoreChart from '../components/charts/AbsoluteScoreChart'
import OutlierChart from '../components/charts/OutlierChart'

import { FaSpinner, FaChartBar, FaStar, FaBrain, FaChartLine, FaChartPie, FaBoxOpen, FaCloud } from 'react-icons/fa'

export default function CategoryAnalysisPage() {
  const [searchParams] = useSearchParams()
  const cat1 = searchParams.get('cat1') || ''
  const cat2 = searchParams.get('cat2') || ''
  const cat3 = searchParams.get('cat3') || ''
  const numReviews = Number(searchParams.get('reviews')) || 10
  const navigate = useNavigate()

  // AI 추천 분석 상태
  const [region, setRegion] = useState('')
  const [season, setSeason] = useState('')
  const [enableRecommendation, setEnableRecommendation] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['category-analysis', cat1, cat2, cat3, numReviews],
    queryFn: () => analyzeCategory(cat1, cat2, cat3, numReviews),
    enabled: !!cat1 && !!cat2 && !!cat3,
    refetchOnMount: true,
  })

  const { data: recommendationData, isLoading: isRecommendationLoading, error: recommendationError } = useQuery({
    queryKey: ['category-recommendation', cat1, cat2, cat3, numReviews, region, season],
    queryFn: () => getRecommendationForCategory(cat1, cat2, cat3, numReviews, region, season),
    enabled: enableRecommendation && !!cat1 && !!cat2 && !!cat3 && !!region && !!season,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <FaSpinner className="animate-spin text-6xl text-primary mx-auto mb-4" />
          <p className="text-xl text-gray-600">
            카테고리 분석 중...
            <br />
            <span className="text-sm">
              {cat1} &gt; {cat2} &gt; {cat3}
              <br />
              여러 축제를 동시에 분석합니다 (5-10분 소요 가능)
            </span>
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <h2 className="text-xl font-bold text-red-800 mb-2">분석 실패</h2>
        <p className="text-red-600">{(error as Error).message}</p>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {cat1} &gt; {cat2} &gt; {cat3}
        </h1>
        <p className="text-gray-600">{data.status}</p>
        <div className="mt-4 flex items-center space-x-4">
          <div className="bg-blue-50 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">전체 축제</span>
            <p className="text-2xl font-bold text-blue-600">
              {data.total_festivals ?? 0}개
            </p>
          </div>
          <div className="bg-green-50 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">분석 완료</span>
            <p className="text-2xl font-bold text-green-600">
              {data.analyzed_festivals ?? 0}개
            </p>
          </div>
        </div>
      </div>

      {/* 카테고리 종합 평가 */}
      {data.category_overall_summary && data.category_overall_summary.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-8 border-l-4 border-blue-500">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <span className="text-3xl mr-2">📝</span>
            카테고리 종합 평가
          </h2>
          <div className="prose prose-lg max-w-none leading-relaxed">
            <style dangerouslySetInnerHTML={{__html: `
              .prose h1, .prose h2, .prose h3, .prose h4 {
                margin-top: 1.5em;
                margin-bottom: 0.75em;
                font-weight: 700;
              }
              .prose p {
                margin-top: 0.75em;
                margin-bottom: 0.75em;
                line-height: 1.8;
              }
              .prose strong {
                color: #1e40af;
                font-weight: 600;
              }
            `}} />
            <ReactMarkdown>{data.category_overall_summary}</ReactMarkdown>
          </div>
        </div>
      )}
      
      {/* 카테고리 주요 불만 사항 */}
      {data.category_negative_summary && data.category_negative_summary.length > 0 && (
        <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-red-800 mb-6 flex items-center">
            <span className="text-3xl mr-2">⚠️</span>
            카테고리 주요 불만 사항
          </h2>
          <div className="prose prose-lg max-w-none">
            <style dangerouslySetInnerHTML={{__html: `
              .prose ol {
                counter-reset: item;
                list-style-type: none;
                padding-left: 0;
              }
              .prose ol > li {
                counter-increment: item;
                margin-top: 1em;
                margin-bottom: 1em;
                padding-left: 2.5em;
                position: relative;
                line-height: 1.8;
              }
              .prose ol > li::before {
                content: counter(item) ".";
                position: absolute;
                left: 0;
                top: 0;
                font-weight: 700;
                color: #dc2626;
                font-size: 1.25em;
              }
              .prose p {
                margin-top: 0.75em;
                margin-bottom: 0.75em;
                line-height: 1.8;
              }
            `}} />
            <ReactMarkdown>{data.category_negative_summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* AI 분석 해석 */}
      {data.distribution_interpretation && data.distribution_interpretation.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <FaBrain className="mr-2 text-purple-600" />
            AI 분석 해석
          </h2>
          <div className="prose prose-lg max-w-none">
            <style dangerouslySetInnerHTML={{__html: `
              .prose h1, .prose h2, .prose h3, .prose h4 {
                margin-top: 1.5em;
                margin-bottom: 0.75em;
                font-weight: 700;
                color: #4c1d95;
              }
              .prose p {
                margin-top: 0.75em;
                margin-bottom: 0.75em;
                line-height: 1.8;
                color: #374151;
              }
              .prose strong {
                color: #7c3aed;
                font-weight: 600;
              }
              .prose ul, .prose ol {
                margin-top: 1em;
                margin-bottom: 1em;
                padding-left: 1.5em;
              }
              .prose li {
                margin-top: 0.5em;
                margin-bottom: 0.5em;
                line-height: 1.7;
              }
            `}} />
            <ReactMarkdown>{data.distribution_interpretation}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* 만족도 및 점수 분포 */}
      <div className="grid md:grid-cols-2 gap-8">
        {/* 만족도 5단계 분포 */}
        {data.satisfaction_counts && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <FaStar className="mr-2 text-yellow-500" />
              카테고리 만족도 5단계 분포
            </h3>
            <SatisfactionChart counts={data.satisfaction_counts} />
            <ExplanationToggle
              title={explanations.satisfactionDistribution.title}
              content={explanations.satisfactionDistribution.content}
            />
          </div>
        )}

        {/* 전체 긍정/부정 비율 */}
        {data.total_pos !== undefined && data.total_neg !== undefined && (
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
              <FaChartBar className="mr-2 text-blue-500" />
              카테고리 전체 긍정/부정 비율
            </h3>
            <DonutChart positive={data.total_pos} negative={data.total_neg} />
            <ExplanationToggle
              title={explanations.overallSentimentRatio.title}
              content={explanations.overallSentimentRatio.content}
            />
          </div>
        )}
      </div>

      {/* 절대 점수 및 이상치 분포 */}
      {data.all_scores && data.all_scores.length > 0 && (
        <div className="grid md:grid-cols-2 gap-6">
          {/* 절대 점수 분포 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center">
              <FaChartPie className="mr-2 text-indigo-500" />
              절대 점수 분포
            </h3>
            <AbsoluteScoreChart scores={data.all_scores} />
            <ExplanationToggle
              title={explanations.absoluteScoreDistribution.title}
              content={explanations.absoluteScoreDistribution.content}
            />
          </div>

          {/* 이상치 분석 */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-xl font-bold mb-4 flex items-center">
              <FaBoxOpen className="mr-2 text-orange-500" />
              이상치 분석 (BoxPlot)
            </h3>
            <OutlierChart scores={data.all_scores} />
            {data.outliers && (
              <p className="text-sm text-gray-500 mt-2">
                총 {data.all_scores.length}개 중 {data.outliers.length}개 이상치 발견
              </p>
            )}
            <ExplanationToggle
              title={explanations.outlierAnalysis.title}
              content={explanations.outlierAnalysis.content}
            />
          </div>
        </div>
      )}

      {/* 트렌드 분석 */}
      {(data.trend_graph || data.focused_trend_graph) && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <FaChartLine className="mr-2 text-indigo-500" />
            카테고리 평균 트렌드 분석
          </h2>
          <div className="grid md:grid-cols-1 lg:grid-cols-2 gap-8">
            {data.trend_graph && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold">전체 트렌드 (1년)</h4>
                  <ExplanationToggle
                    title={explanations.overallTrend.title}
                    content={explanations.overallTrend.content}
                  />
                </div>
                <img src={data.trend_graph} alt="전체 트렌드 그래프" className="w-full rounded-lg shadow-sm" />
              </div>
            )}
            {data.focused_trend_graph && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-bold">집중 트렌드 (축제 기간 중심)</h4>
                  <ExplanationToggle
                    title={explanations.focusedTrend.title}
                    content={explanations.focusedTrend.content}
                  />
                </div>
                <img src={data.focused_trend_graph} alt="집중 트렌드 그래프" className="w-full rounded-lg shadow-sm" />
              </div>
            )}
          </div>
        </div>
      )}

      {/* 계절별 분석 */}
      {data.seasonal_data && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">계절별 분석</h2>
          <SeasonalTabs
            seasonalData={data.seasonal_data}
            seasonalWordClouds={data.seasonal_word_clouds}
          />
        </div>
      )}

      {/* 블로그 내용 기반 계절별 키워드 */}
      {data.keyword_wordclouds && <BlogKeywordWordclouds keywordWordclouds={data.keyword_wordclouds} />}

      {/* 개별 축제 분석 결과 */}
      {data.individual_results && data.individual_results.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-bold">개별 축제 분석 결과</h2>
            <ExplanationToggle
              title={explanations.trendIndex.title}
              content={explanations.trendIndex.content}
            />
          </div>
          <div className="grid gap-6">
            {data.individual_results.map((festival: any, index: number) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer"
                onClick={() => navigate(`/analysis/${encodeURIComponent(festival['축제명'])}?reviews=${numReviews}`)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-xl font-bold text-gray-900">
                      {festival['축제명']}
                    </h3>
                    <p className="text-sm text-gray-500">
                      기간: {festival['축제 기간 (일)']}일
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">감성 점수</div>
                    <div className="text-2xl font-bold text-primary">
                      {festival['감성 점수']}
                    </div>
                  </div>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                  <div className="bg-green-50 p-3 rounded">
                    <div className="text-xs text-gray-600">긍정 비율</div>
                    <div className="text-lg font-bold text-green-600">
                      {festival['긍정 비율 (%)']}%
                    </div>
                  </div>
                  <div className="bg-red-50 p-3 rounded">
                    <div className="text-xs text-gray-600">부정 비율</div>
                    <div className="text-lg font-bold text-red-600">
                      {festival['부정 비율 (%)']}%
                    </div>
                  </div>
                  <div className="bg-purple-50 p-3 rounded">
                    <div className="text-xs text-gray-600">트렌드 지수</div>
                    <div className="text-lg font-bold text-purple-600">
                      {festival['트렌드 지수 (%)']}%
                    </div>
                  </div>
                </div>

                {festival['주요 불만 사항 요약'] && (
                  <div className="mt-4 bg-gradient-to-br from-yellow-50 to-orange-50 p-4 rounded-lg border border-yellow-200">
                    <div className="flex items-center mb-2">
                      <span className="text-xl mr-2">⚠️</span>
                      <div className="text-sm font-bold text-yellow-800">
                        주요 불만 사항
                      </div>
                    </div>
                    <div className="prose prose-sm max-w-none">
                      <style dangerouslySetInnerHTML={{__html: `
                        .prose ol {
                          counter-reset: item;
                          list-style-type: none;
                          padding-left: 0;
                        }
                        .prose ol > li {
                          counter-increment: item;
                          margin-top: 0.5em;
                          margin-bottom: 0.5em;
                          padding-left: 2em;
                          position: relative;
                          line-height: 1.6;
                        }
                        .prose ol > li::before {
                          content: counter(item) ".";
                          position: absolute;
                          left: 0;
                          top: 0;
                          font-weight: 700;
                          color: #d97706;
                          font-size: 1.1em;
                        }
                        .prose p {
                          margin-top: 0.5em;
                          margin-bottom: 0.5em;
                          line-height: 1.6;
                        }
                      `}} />
                      <ReactMarkdown>{festival['주요 불만 사항 요약']}</ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* AI 총합 분석 추천 */}
      <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">🤖 AI 총합 분석 추천</h2>
        <p className="text-gray-600 mb-6">
          지역과 계절을 입력하면 AI가 해당 조건에서 이 카테고리 축제들의 성공 가능성과 기획 방향을 분석해드립니다.
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
                {isRecommendationLoading ? 'AI 분석 중...' : 'AI 추천 분석 시작'}
              </button>
            </div>
          </div>
        </div>

        {/* 추천 결과 표시 */}
        {isRecommendationLoading && (
          <div className="bg-white rounded-lg p-8 text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mx-auto mb-4"></div>
            <p className="text-gray-600">AI가 분석 중입니다...</p>
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
    </div>
  )
}

// 블로그 내용 기반 계절별 키워드 워드클라우드 컴포넌트
function BlogKeywordWordclouds({ keywordWordclouds }: { keywordWordclouds: Record<string, string | null> }) {
  const [activeSeason, setActiveSeason] = useState('봄')

  const seasons = [
    { name: '봄', activeClass: 'bg-pink-500 text-white shadow-lg', hoverClass: 'bg-gray-100 text-gray-700 hover:bg-pink-100', icon: '🌸' },
    { name: '여름', activeClass: 'bg-green-500 text-white shadow-lg', hoverClass: 'bg-gray-100 text-gray-700 hover:bg-green-100', icon: '🌻' },
    { name: '가을', activeClass: 'bg-orange-500 text-white shadow-lg', hoverClass: 'bg-gray-100 text-gray-700 hover:bg-orange-100', icon: '🍂' },
    { name: '겨울', activeClass: 'bg-blue-500 text-white shadow-lg', hoverClass: 'bg-gray-100 text-gray-700 hover:bg-blue-100', icon: '❄️' }
  ]

  // 유효한 계절 필터링 (워드클라우드가 있는 계절만)
  const validSeasons = seasons.filter(season => keywordWordclouds[season.name])

  if (validSeasons.length === 0) return null

  // 기본 활성 계절 설정
  if (!keywordWordclouds[activeSeason] && validSeasons.length > 0) {
    setActiveSeason(validSeasons[0].name)
  }

  return (
    <div className="bg-white rounded-xl shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center">
          <FaCloud className="mr-2 text-purple-500" />
          블로그 내용 기반 계절별 키워드
        </h2>
        <ExplanationToggle
          title="블로그 키워드 분석"
          content="각 축제의 블로그 리뷰에서 추출한 키워드를 계절별로 분류하여 빈도수 기반 워드클라우드로 시각화했습니다. 크기가 클수록 더 자주 언급된 키워드입니다."
        />
      </div>

      {/* 계절 탭 */}
      <div className="flex gap-2 mb-6 overflow-x-auto">
        {validSeasons.map((season) => (
          <button
            key={season.name}
            onClick={() => setActiveSeason(season.name)}
            className={`px-6 py-3 rounded-lg font-semibold transition flex items-center gap-2 whitespace-nowrap ${
              activeSeason === season.name ? season.activeClass : season.hoverClass
            }`}
          >
            <span className="text-2xl">{season.icon}</span>
            <span>{season.name}</span>
          </button>
        ))}
      </div>

      {/* 워드클라우드 표시 */}
      <div className="bg-gray-50 rounded-lg p-6">
        {keywordWordclouds[activeSeason] ? (
          <div className="flex flex-col items-center">
            <img
              src={keywordWordclouds[activeSeason]!}
              alt={`${activeSeason} 키워드 워드클라우드`}
              className="max-w-full h-auto rounded-lg shadow-md"
            />
            <p className="mt-4 text-sm text-gray-600 text-center">
              {activeSeason} 계절 축제 블로그에서 가장 많이 언급된 키워드들
            </p>
          </div>
        ) : (
          <div className="text-center text-gray-500 py-12">
            {activeSeason} 계절 데이터가 없습니다
          </div>
        )}
      </div>
    </div>
  )
}
