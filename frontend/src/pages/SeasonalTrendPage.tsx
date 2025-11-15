import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getSeasonalTrends, getFestivalTrend } from '../lib/api'
import { FaCloudSun, FaSun, FaLeaf, FaSnowflake, FaSearch, FaLayerGroup } from 'react-icons/fa'

type Season = '봄' | '여름' | '가을' | '겨울'

const SEASONS: { value: Season; label: string; icon: JSX.Element; color: string }[] = [
  { value: '봄', label: '봄 (3-5월)', icon: <FaCloudSun />, color: 'bg-pink-500' },
  { value: '여름', label: '여름 (6-8월)', icon: <FaSun />, color: 'bg-yellow-500' },
  { value: '가을', label: '가을 (9-11월)', icon: <FaLeaf />, color: 'bg-orange-500' },
  { value: '겨울', label: '겨울 (12-2월)', icon: <FaSnowflake />, color: 'bg-blue-500' },
]

export default function SeasonalTrendPage() {
  const navigate = useNavigate()
  const [selectedSeason, setSelectedSeason] = useState<Season>('봄')
  const [selectedFestival, setSelectedFestival] = useState<string>('')

  // 계절별 트렌드 데이터 fetch
  const {
    data: seasonalData,
    isLoading: isSeasonalLoading,
    error: seasonalError,
  } = useQuery({
    queryKey: ['seasonal-trends', selectedSeason],
    queryFn: () => getSeasonalTrends(selectedSeason),
    enabled: !!selectedSeason,
  })

  // 개별 축제 트렌드 fetch
  const {
    data: festivalData,
    isLoading: isFestivalLoading,
    refetch: refetchFestivalTrend,
  } = useQuery({
    queryKey: ['festival-trend', selectedFestival, selectedSeason],
    queryFn: () => getFestivalTrend(selectedFestival, selectedSeason),
    enabled: false, // 수동 실행
  })

  const handleViewFestivalTrend = () => {
    if (!selectedFestival) {
      alert('축제를 선택해주세요')
      return
    }
    refetchFestivalTrend()
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">계절별 인기 축제 탐색</h1>
        <p className="text-gray-600">
          계절별로 인기 있는 축제를 검색량 기반으로 확인하세요
        </p>
      </div>

      {/* Season Selection */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">계절 선택</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {SEASONS.map((season) => (
            <button
              key={season.value}
              onClick={() => {
                setSelectedSeason(season.value)
                setSelectedFestival('')
              }}
              className={`p-6 rounded-lg border-2 transition ${
                selectedSeason === season.value
                  ? `${season.color} text-white border-transparent`
                  : 'bg-white text-gray-700 border-gray-300 hover:border-gray-400'
              }`}
            >
              <div className="flex flex-col items-center space-y-2">
                <div className="text-3xl">{season.icon}</div>
                <div className="font-semibold">{season.label}</div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {isSeasonalLoading && (
        <div className="bg-white rounded-xl shadow-md p-12 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">분석 중...</p>
        </div>
      )}

      {/* Error State */}
      {seasonalError && (
        <div className="bg-red-50 rounded-xl p-6 text-center">
          <p className="text-red-600">
            데이터를 불러오는 중 오류가 발생했습니다.
            <br />
            트렌드 데이터가 수집되어 있는지 확인해주세요.
          </p>
        </div>
      )}

      {/* Results */}
      {seasonalData && !isSeasonalLoading && (
        <div className="space-y-8">
          {/* Wordcloud */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">
              {selectedSeason} 시즌 워드클라우드
            </h2>
            <div className="flex justify-center">
              <img
                src={seasonalData.wordcloud_url}
                alt={`${selectedSeason} 워드클라우드`}
                className="max-w-full h-auto rounded-lg"
              />
            </div>
          </div>

          {/* Timeline Graph */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">
              상위 10개 축제 타임라인 & 검색량
            </h2>
            <div className="flex justify-center">
              <img
                src={seasonalData.timeline_url}
                alt={`${selectedSeason} 타임라인`}
                className="max-w-full h-auto rounded-lg"
              />
            </div>
          </div>

          {/* Table */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">상세 정보 테이블</h2>
            <p className="text-sm text-gray-600 mb-4">
              💡 <strong>Tip:</strong> 축제명을 클릭하여 상세 분석 페이지로 바로 이동하세요!
            </p>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      순위
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      축제명
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      최대 검색량
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      평균 검색량
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      행사 기간
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      분석
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {seasonalData.top_festivals.map((festival) => {
                    const handleNavigate = () => {
                      const navigationState = {
                        keyword: festival.축제명,
                        cat1: festival.cat1,
                        cat2: festival.cat2,
                        cat3: festival.cat3,
                      }
                      console.log('Navigating to /search with state:', navigationState)
                      navigate('/search', { state: navigationState })
                    }

                    return (
                      <tr key={festival.순위} className="hover:bg-gray-50 transition">
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {festival.순위}
                        </td>
                        <td
                          className="px-6 py-4 whitespace-nowrap text-sm text-blue-600 font-semibold cursor-pointer hover:text-blue-800 hover:underline"
                          onClick={handleNavigate}
                          title="클릭하여 검색 페이지로 이동"
                        >
                          {festival.축제명}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {festival['최대 검색량'].toFixed(1)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {festival['평균 검색량'].toFixed(1)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {festival['행사 시작일']} ~ {festival['행사 종료일']}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                          <button
                            onClick={handleNavigate}
                            className="inline-flex items-center px-3 py-1.5 bg-blue-500 text-white text-xs font-medium rounded-md hover:bg-blue-600 transition"
                            title="검색 페이지로 이동 (후기 개수 선택 가능)"
                          >
                            <FaSearch className="mr-1" />
                            상세 분석
                          </button>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Individual Festival Trend */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">개별 축제 트렌드 분석</h2>
            <p className="text-gray-600 mb-4">
              흥미로운 축제를 선택하여 상세 트렌드를 확인하세요
            </p>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  축제 선택
                </label>
                <select
                  value={selectedFestival}
                  onChange={(e) => setSelectedFestival(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
                >
                  <option value="">선택하세요</option>
                  {seasonalData.festival_names.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={handleViewFestivalTrend}
                disabled={!selectedFestival || isFestivalLoading}
                className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {isFestivalLoading ? '로딩 중...' : '이 축제 트렌드 보기'}
              </button>
            </div>

            {/* Festival Trend Graph */}
            {festivalData && (
              <div className="mt-6">
                <h3 className="text-xl font-bold mb-3">
                  {festivalData.festival_name} 검색 트렌드
                </h3>
                <div className="flex justify-center">
                  <img
                    src={festivalData.trend_graph_url}
                    alt={`${festivalData.festival_name} 트렌드`}
                    className="max-w-full h-auto rounded-lg"
                  />
                </div>
                <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-700 mb-3">
                    💡 <strong>더 자세한 분석이 필요하신가요?</strong>
                    <br />
                    블로그 감성 분석, 워드클라우드, LLM 요약 등 모든 기능을 활용하세요!
                  </p>
                  <button
                    onClick={() => {
                      // 선택된 축제의 카테고리 정보 찾기
                      const festivalInfo = seasonalData.top_festivals.find(
                        (f) => f.축제명 === festivalData.festival_name
                      )
                      const categoryParams = festivalInfo
                        ? `${festivalInfo.cat1 ? `&cat1=${encodeURIComponent(festivalInfo.cat1)}` : ''}${
                            festivalInfo.cat2 ? `&cat2=${encodeURIComponent(festivalInfo.cat2)}` : ''
                          }${festivalInfo.cat3 ? `&cat3=${encodeURIComponent(festivalInfo.cat3)}` : ''}`
                        : ''
                      navigate(`/search?keyword=${encodeURIComponent(festivalData.festival_name)}${categoryParams}`)
                    }}
                    className="w-full inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition"
                  >
                    <FaSearch className="mr-2" />
                    &quot;{festivalData.festival_name}&quot; 상세 분석 시작
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
