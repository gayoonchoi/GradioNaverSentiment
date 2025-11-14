import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { analyzeComparison } from '../lib/api'
import DonutChart from '../components/charts/DonutChart'
import SatisfactionChart from '../components/charts/SatisfactionChart'
import { FaSpinner, FaBalanceScale } from 'react-icons/fa'
import ReactMarkdown from 'react-markdown'

export default function ComparisonPage() {
  const [keywordA, setKeywordA] = useState('')
  const [keywordB, setKeywordB] = useState('')
  const [numReviews, setNumReviews] = useState(10)
  const [startAnalysis, setStartAnalysis] = useState(false)

  const { data, isLoading, error } = useQuery({
    queryKey: ['comparison', keywordA, keywordB, numReviews],
    queryFn: () => analyzeComparison(keywordA, keywordB, numReviews),
    enabled: startAnalysis && !!keywordA && !!keywordB,
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
    <div className="space-y-8">
      {/* 입력 폼 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-6">
          축제 비교 분석
        </h1>
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
    </div>
  )
}
