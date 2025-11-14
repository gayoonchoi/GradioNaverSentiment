import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { analyzeCategory } from '../lib/api'
import DonutChart from '../components/charts/DonutChart'

import { FaSpinner, FaCheckCircle } from 'react-icons/fa'

export default function CategoryAnalysisPage() {
  const [searchParams] = useSearchParams()
  const cat1 = searchParams.get('cat1') || ''
  const cat2 = searchParams.get('cat2') || ''
  const cat3 = searchParams.get('cat3') || ''
  const numReviews = Number(searchParams.get('reviews')) || 10
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery({
    queryKey: ['category-analysis', cat1, cat2, cat3, numReviews],
    queryFn: () => analyzeCategory(cat1, cat2, cat3, numReviews),
    enabled: !!cat1 && !!cat2 && !!cat3,
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
              {data.total_festivals}개
            </p>
          </div>
          <div className="bg-green-50 px-4 py-2 rounded-lg">
            <span className="text-sm text-gray-600">분석 완료</span>
            <p className="text-2xl font-bold text-green-600">
              {data.analyzed_festivals}개
            </p>
          </div>
        </div>
      </div>

      {/* 카테고리 종합 요약 */}
      {data.overall_summary && data.overall_summary.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-4 flex items-center">
            <FaCheckCircle className="text-green-500 mr-2" />
            카테고리 종합 요약
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {data.overall_summary.map((item: any, index: number) => (
              <div key={index} className="bg-white rounded-lg p-4 shadow">
                <h3 className="font-bold text-gray-700 mb-2">{item['항목']}</h3>
                <p className="text-2xl font-bold text-primary">{item['값']}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 개별 축제 분석 결과 */}
      {data.individual_results && data.individual_results.length > 0 && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">개별 축제 분석 결과</h2>
          <div className="grid gap-6">
            {data.individual_results.map((festival: any, index: number) => (
              <div
                key={index}
                className="border border-gray-200 rounded-lg p-6 hover:shadow-lg transition cursor-pointer"
                onClick={() => navigate(`/analysis/${festival['축제명']}?reviews=${numReviews}`)}
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
                  <div className="mt-4 bg-yellow-50 p-3 rounded">
                    <div className="text-xs text-gray-600 mb-1">
                      주요 불만 사항
                    </div>
                    <div className="text-sm text-gray-800">
                      {festival['주요 불만 사항 요약']}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 계절별 데이터 (있을 경우) */}
      {data.seasonal_data && (
        <div className="bg-white rounded-xl shadow-md p-6">
          <h2 className="text-2xl font-bold mb-4">계절별 분석</h2>
          <div className="grid md:grid-cols-4 gap-4">
            {Object.entries(data.seasonal_data).map(([season, stats]: [string, any]) => {
              if (season === '정보없음') return null
              const total = stats.pos + stats.neg
              if (total === 0) return null

              return (
                <div key={season} className="border rounded-lg p-4">
                  <h3 className="text-lg font-bold mb-3 text-center">
                    {season === '봄' && '🌸'}
                    {season === '여름' && '☀️'}
                    {season === '가을' && '🍁'}
                    {season === '겨울' && '❄️'}
                    {' ' + season}
                  </h3>
                  <DonutChart positive={stats.pos} negative={stats.neg} />
                  <div className="text-center mt-2 text-sm text-gray-600">
                    총 {total}개 리뷰
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
