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

export default function AnalysisPage() {
  const { keyword } = useParams<{ keyword: string }>()
  const [searchParams] = useSearchParams()
  const numReviews = Number(searchParams.get('reviews')) || 10

  const { data, isLoading, error } = useQuery({
    queryKey: ['analysis', keyword, numReviews],
    queryFn: () => analyzeKeyword(keyword!, numReviews),
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
        <div className="mt-4 flex items-center space-x-4">
          <div className="bg-blue-50 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">긍정</span>
            <p className="text-2xl font-bold text-blue-600">{data.total_pos}</p>
          </div>
          <div className="bg-red-50 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">부정</span>
            <p className="text-2xl font-bold text-red-600">{data.total_neg}</p>
          </div>
          <div className="bg-green-50 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">평균 만족도</span>
            <p className="text-2xl font-bold text-green-600">
              {data.avg_satisfaction.toFixed(2)} / 5.0
            </p>
          </div>
        </div>
      </div>

      {/* LLM 분포 해석 */}
      {data.distribution_interpretation && (
        <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            🤖 AI 분석 해석
          </h2>
          <div className="prose max-w-none">
            <ReactMarkdown>{data.distribution_interpretation}</ReactMarkdown>
          </div>
        </div>
      )}

      {/* 차트 그리드 */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* 도넛 차트 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">전체 긍정/부정 비율</h3>
          <DonutChart positive={data.total_pos} negative={data.total_neg} />
        </div>

        {/* 만족도 5단계 차트 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">만족도 5단계 분포</h3>
          <SatisfactionChart counts={data.satisfaction_counts} />
        </div>

        {/* 절대 점수 분포 */}
        <div className="bg-white rounded-xl shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">절대 점수 분포</h3>
          <AbsoluteScoreChart scores={data.all_scores} />
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
        </div>
      </div>

      {/* 계절별 분석 */}
      {data.seasonal_data && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">계절별 분석</h2>
          <SeasonalTabs seasonalData={data.seasonal_data} />
        </div>
      )}

      {/* 블로그 결과 테이블 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">개별 블로그 분석 결과</h2>
        <BlogTable blogs={data.blog_results} pageSize={5} />
      </div>

      {/* URL 목록 */}
      {data.url_markdown && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <ReactMarkdown className="prose max-w-none">
            {data.url_markdown}
          </ReactMarkdown>
        </div>
      )}
    </div>
  )
}
