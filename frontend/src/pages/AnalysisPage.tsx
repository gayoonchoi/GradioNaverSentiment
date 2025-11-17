import { useParams, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { analyzeKeyword } from '../lib/api'
import SatisfactionChart from '../components/charts/SatisfactionChart'
import OutlierChart from '../components/charts/OutlierChart'
import AbsoluteScoreChart from '../components/charts/AbsoluteScoreChart'
import DonutChart from '../components/charts/DonutChart'
import SeasonalTabs from '../components/seasonal/SeasonalTabs'
import BlogTable from '../components/BlogTable'
import LoadingSpinner from '../components/LoadingSpinner'
import ErrorDisplay from '../components/ErrorDisplay'
import ReactMarkdown from 'react-markdown'
import ExplanationToggle from '../components/common/ExplanationToggle' // Import ExplanationToggle
import { explanations } from '../lib/explanations' // Import explanations

export default function AnalysisPage() {
  const { keyword: encodedKeyword } = useParams<{ keyword: string }>()
  const keyword = encodedKeyword ? decodeURIComponent(encodedKeyword) : ''
  const [searchParams] = useSearchParams()
  const numReviews = Number(searchParams.get('reviews')) || 10

  const { data, isLoading, error } = useQuery({
    queryKey: ['analysis', keyword, numReviews],
    queryFn: () => analyzeKeyword(keyword, numReviews),
    enabled: !!keyword,
  })

  if (isLoading) {
    return (
      <LoadingSpinner
        message={`${keyword} 분석 중...`}
        subtitle="네이버 블로그 크롤링 및 AI 감성 분석 진행 중 (최대 2-3분 소요)"
      />
    )
  }

  if (error) {
    return <ErrorDisplay message={(error as Error).message} />
  }

  if (!data) return null

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">{keyword}</h1>
        <p className="text-gray-600">{data.status}</p>
        <div className="mt-4 flex items-start space-x-4">
          <div className="bg-blue-50 px-4 py-2 rounded-lg min-h-[80px] flex flex-col justify-center">
            <span className="text-sm text-gray-600">긍정</span>
            <p className="text-2xl font-bold text-blue-600">{data.total_pos}</p>
          </div>
          <div className="bg-red-50 px-4 py-2 rounded-lg min-h-[80px] flex flex-col justify-center">
            <span className="text-sm text-gray-600">부정</span>
            <p className="text-2xl font-bold text-red-600">{data.total_neg}</p>
          </div>
          <div className="bg-green-50 px-4 py-2 rounded-lg min-h-[80px] flex-1 flex flex-col">
            <span className="text-sm text-gray-600">평균 만족도</span>
            <p className="text-2xl font-bold text-green-600">
              {data.avg_satisfaction.toFixed(2)} / 5.0
            </p>
            <div className="mt-1">
              <ExplanationToggle
                title={explanations.sentimentScore.title}
                content={explanations.sentimentScore.content}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 상세 정보 요약 */}
      <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl shadow-md p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">📋 상세 정보 요약</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">📍</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-1">주소</p>
                <p className="text-base text-gray-800 leading-relaxed">{data.addr1} {data.addr2}</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">🗓️</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-1">축제 기간</p>
                <p className="text-base text-gray-800 leading-relaxed">{data.eventStartDate} ~ {data.eventEndDate}</p>
                <p className="text-sm text-primary font-semibold">({data.eventPeriod}일간)</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">💯</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-1">종합 감성 점수</p>
                <p className="text-xl font-bold text-green-600">{data.sentiment_score.toFixed(2)} / 100</p>
                <div className="mt-2">
                  <ExplanationToggle
                    title={explanations.sentimentScore.title}
                    content={explanations.sentimentScore.content}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">📈</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-1">트렌드 지수</p>
                <p className="text-xl font-bold text-purple-600">{data.trend_metrics.trend_index.toFixed(2)}</p>
                <div className="mt-2">
                  <ExplanationToggle
                    title={explanations.trendIndex.title}
                    content={explanations.trendIndex.content}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">📊</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-1">만족도 변화</p>
                <p className={`text-xl font-bold ${data.satisfaction_delta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {data.satisfaction_delta >= 0 ? '+' : ''}{data.satisfaction_delta.toFixed(2)}
                </p>
                <div className="mt-2">
                  <ExplanationToggle
                    title={explanations.satisfactionDelta.title}
                    content={explanations.satisfactionDelta.content}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition">
            <div className="flex items-start space-x-3">
              <span className="text-2xl">🔑</span>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-600 mb-1">주요 감성어 (Top 3)</p>
                <p className="text-base text-gray-800 leading-relaxed">
                  {Object.keys(data.emotion_keyword_freq).length > 0
                    ? Object.entries(data.emotion_keyword_freq).slice(0, 3).map(([key, value]) => `${key}(${value})`).join(', ')
                    : '추출된 감성어 없음'}
                </p>
                <div className="mt-2">
                  <ExplanationToggle
                    title={explanations.emotionKeywordFreq.title}
                    content={explanations.emotionKeywordFreq.content}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 총합 평가 */}
      {data.overall_summary && data.overall_summary.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg p-8 border-l-4 border-blue-500">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center">
            <span className="text-3xl mr-2">📝</span>
            총합 평가
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
              .prose ol, .prose ul {
                margin-top: 1em;
                margin-bottom: 1em;
              }
              .prose li {
                margin-top: 0.5em;
                margin-bottom: 0.5em;
                line-height: 1.7;
              }
              .prose strong {
                color: #1e40af;
                font-weight: 600;
              }
            `}} />
            <ReactMarkdown>{data.overall_summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* LLM 분포 해석 */}
      {data.distribution_interpretation && data.distribution_interpretation.length > 0 && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            🤖 AI 분석 해석
          </h2>
          <div className="prose max-w-none">
            <ReactMarkdown>{data.distribution_interpretation}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* 주요 불만 사항 */}
      {data.negative_summary && data.negative_summary.length > 0 && (
        <div className="bg-gradient-to-br from-red-50 to-orange-50 rounded-xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-red-800 mb-6 flex items-center">
            <span className="text-3xl mr-2">⚠️</span>
            주요 불만 사항
          </h2>
          <div className="prose prose-lg max-w-none">
            <style dangerouslySetInnerHTML={{__html: `
              .prose h1, .prose h2, .prose h3, .prose h4 {
                margin-top: 1.5em;
                margin-bottom: 0.75em;
                font-weight: 700;
                color: #991b1b;
              }
              .prose p {
                margin-top: 0.75em;
                margin-bottom: 0.75em;
                line-height: 1.8;
              }
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
                background: white;
                width: 2em;
                height: 2em;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
              }
              .prose ul > li {
                margin-top: 0.75em;
                margin-bottom: 0.75em;
                padding-left: 0.5em;
                line-height: 1.8;
              }
              .prose strong {
                color: #b91c1c;
                font-weight: 600;
              }
            `}} />
            <ReactMarkdown>{data.negative_summary}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* 차트 그리드 */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* 도넛 차트 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">전체 긍정/부정 비율</h3>
          <DonutChart positive={data.total_pos} negative={data.total_neg} />
          <ExplanationToggle
            title={explanations.overallSentimentRatio.title}
            content={explanations.overallSentimentRatio.content}
          />
        </div>

        {/* 만족도 5단계 차트 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">만족도 5단계 분포</h3>
          <SatisfactionChart counts={data.satisfaction_counts} />
          <ExplanationToggle
            title={explanations.satisfactionDistribution.title}
            content={explanations.satisfactionDistribution.content}
          />
        </div>

        {/* 절대 점수 분포 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">절대 점수 분포</h3>
          <AbsoluteScoreChart scores={data.all_scores} />
          <ExplanationToggle
            title={explanations.absoluteScoreDistribution.title}
            content={explanations.absoluteScoreDistribution.content}
          />
        </div>

        {/* 이상치 분석 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">
            이상치 분석 (BoxPlot)
          </h3>
          <OutlierChart scores={data.all_scores} />
          <p className="text-sm text-gray-500 mt-2">
            총 {data.all_scores.length}개 중 {data.outliers.length}개 이상치 발견
          </p>
          <ExplanationToggle
            title={explanations.outlierAnalysis.title}
            content={explanations.outlierAnalysis.content}
          />
        </div>
      </div>

      {/* 트렌드 분석 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">트렌드 분석</h2>
        <div className="grid md:grid-cols-2 gap-6">
          {data.focused_trend_graph && (
            <div>
              <h3 className="text-xl font-bold mb-4">집중 트렌드 (축제 기간 중심)</h3>
              <img
                src={data.focused_trend_graph}
                alt="집중 트렌드 그래프"
                className="w-full h-auto rounded-lg border"
              />
              <ExplanationToggle
                title={explanations.focusedTrend.title}
                content={explanations.focusedTrend.content}
              />
            </div>
          )}
          {data.trend_graph && (
            <div>
              <h3 className="text-xl font-bold mb-4">전체 트렌드 (1년)</h3>
              <img
                src={data.trend_graph}
                alt="전체 트렌드 그래프"
                className="w-full h-auto rounded-lg border"
              />
              <ExplanationToggle
                title={explanations.overallTrend.title}
                content={explanations.overallTrend.content}
              />
            </div>
          )}
        </div>
      </div>

      {/* 계절별 분석 */}
      {data.seasonal_data && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">계절별 분석</h2>
          <ExplanationToggle
            title={explanations.seasonalAnalysis.title}
            content={explanations.seasonalAnalysis.content}
          />
          <SeasonalTabs
            seasonalData={data.seasonal_data}
            seasonalWordClouds={data.seasonal_word_clouds}
          />
        </div>
      )}

      {/* 블로그 결과 테이블 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">개별 블로그 분석 결과</h2>
        <BlogTable blogs={data.blog_results} pageSize={5} />
      </div>
    </div>
  )
}
