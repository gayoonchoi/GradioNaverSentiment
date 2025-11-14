import { useState } from 'react'
import { FaSeedling, FaSun, FaLeaf, FaSnowflake } from 'react-icons/fa'

interface SeasonalTabsProps {
  seasonalData: {
    봄: { pos: number; neg: number }
    여름: { pos: number; neg: number }
    가을: { pos: number; neg: number }
    겨울: { pos: number; neg: number }
    정보없음?: { pos: number; neg: number }
  }
  seasonalWordClouds?: {
    봄?: { positive?: string; negative?: string }
    여름?: { positive?: string; negative?: string }
    가을?: { positive?: string; negative?: string }
    겨울?: { positive?: string; negative?: string }
  }
}

const SEASON_CONFIG = {
  봄: { icon: FaSeedling, color: 'text-green-500', bg: 'bg-green-50' },
  여름: { icon: FaSun, color: 'text-yellow-500', bg: 'bg-yellow-50' },
  가을: { icon: FaLeaf, color: 'text-orange-500', bg: 'bg-orange-50' },
  겨울: { icon: FaSnowflake, color: 'text-blue-500', bg: 'bg-blue-50' },
}

export default function SeasonalTabs({
  seasonalData,
  seasonalWordClouds = {},
}: SeasonalTabsProps) {
  const seasons = Object.keys(SEASON_CONFIG) as Array<keyof typeof SEASON_CONFIG>
  const availableSeasons = seasons.filter((season) => {
    const data = seasonalData[season]
    return data && (data.pos > 0 || data.neg > 0)
  })
  
  const [activeSeason, setActiveSeason] = useState<string>(availableSeasons[0] || '봄')

  if (availableSeasons.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        계절별 데이터가 없습니다
      </div>
    )
  }

  const currentData = seasonalData[activeSeason as keyof typeof seasonalData]
  const currentWordClouds = seasonalWordClouds[activeSeason as keyof typeof seasonalWordClouds]

  return (
    <div className="space-y-4">
      {/* 탭 버튼 */}
      <div className="flex space-x-2 border-b border-gray-200">
        {availableSeasons.map((season) => {
          const config = SEASON_CONFIG[season]
          const Icon = config.icon
          const isActive = activeSeason === season

          return (
            <button
              key={season}
              onClick={() => setActiveSeason(season)}
              className={`flex items-center space-x-2 px-6 py-3 font-semibold transition ${
                isActive
                  ? `${config.color} border-b-2 border-current`
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Icon />
              <span>{season}</span>
            </button>
          )
        })}
      </div>

      {/* 탭 내용 */}
      <div className={`${SEASON_CONFIG[activeSeason as keyof typeof SEASON_CONFIG].bg} rounded-xl p-6`}>
        {/* 통계 */}
        <div className="grid md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="text-sm text-gray-600">긍정 문장</div>
            <div className="text-3xl font-bold text-green-600">
              {currentData?.pos || 0}개
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="text-sm text-gray-600">부정 문장</div>
            <div className="text-3xl font-bold text-red-600">
              {currentData?.neg || 0}개
            </div>
          </div>
          <div className="bg-white rounded-lg p-4 shadow">
            <div className="text-sm text-gray-600">긍정 비율</div>
            <div className="text-3xl font-bold text-blue-600">
              {currentData
                ? (
                    ((currentData.pos + currentData.neg > 0
                      ? currentData.pos / (currentData.pos + currentData.neg)
                      : 0) * 100
                  ).toFixed(1))
                : 0}
              %
            </div>
          </div>
        </div>

        {/* 워드클라우드 */}
        {currentWordClouds && (
          <div className="grid md:grid-cols-2 gap-6">
            {currentWordClouds.positive && (
              <div className="bg-white rounded-lg p-4 shadow">
                <h4 className="text-lg font-bold text-green-600 mb-3">
                  긍정 키워드
                </h4>
                <img
                  src={currentWordClouds.positive}
                  alt={`${activeSeason} 긍정 워드클라우드`}
                  className="w-full h-auto rounded"
                />
              </div>
            )}
            {currentWordClouds.negative && (
              <div className="bg-white rounded-lg p-4 shadow">
                <h4 className="text-lg font-bold text-red-600 mb-3">
                  부정 키워드
                </h4>
                <img
                  src={currentWordClouds.negative}
                  alt={`${activeSeason} 부정 워드클라우드`}
                  className="w-full h-auto rounded"
                />
              </div>
            )}
          </div>
        )}

        {!currentWordClouds && (
          <div className="bg-white rounded-lg p-8 text-center text-gray-500">
            워드클라우드 데이터가 없습니다
          </div>
        )}
      </div>
    </div>
  )
}
