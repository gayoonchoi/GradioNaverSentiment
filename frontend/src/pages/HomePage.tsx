import { Link } from 'react-router-dom'
import { FaChartLine, FaLayerGroup, FaRandom, FaUsers } from 'react-icons/fa'
import { motion } from 'framer-motion'

export default function HomePage() {
  const features = [
    {
      icon: <FaChartLine className="text-4xl text-primary" />,
      title: '단일 키워드 분석',
      description: '축제명으로 네이버 블로그 리뷰를 수집하고 만족도 5단계 분석',
    },
    {
      icon: <FaLayerGroup className="text-4xl text-green-500" />,
      title: '카테고리별 분석',
      description: '계절/테마별 축제를 한번에 분석하여 카테고리 트렌드 파악',
    },
    {
      icon: <FaRandom className="text-4xl text-purple-500" />,
      title: '축제 비교 분석',
      description: '2개 축제를 비교하여 강점과 약점을 한눈에 확인',
    },
    {
      icon: <FaUsers className="text-4xl text-orange-500" />,
      title: '자유 그룹 비교',
      description: '최대 4개 그룹을 자유롭게 구성하여 맞춤 비교 분석',
    },
  ]

  return (
    <div className="space-y-12">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <h1 className="text-5xl font-bold text-gray-900">
          데이터 기반 축제 기획을 위한
          <br />
          <span className="text-primary">감성 분석 플랫폼</span>
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          네이버 블로그 리뷰를 AI가 분석하여 관람객의 만족도, 불만 사항, 계절별
          트렌드까지 한눈에 파악하세요
        </p>
        <div className="pt-4">
          <Link
            to="/search"
            className="inline-block bg-primary text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-blue-600 transition shadow-lg"
          >
            지금 시작하기 →
          </Link>
        </div>
      </motion.div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-2 gap-6 pt-8">
        {features.map((feature, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-white p-6 rounded-xl shadow-md hover:shadow-xl transition"
          >
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0">{feature.icon}</div>
              <div>
                <h3 className="text-xl font-bold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* What You Get Section */}
      <div className="bg-white rounded-xl shadow-md p-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-6 text-center">
          FestInsight가 제공하는 분석
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-4xl mb-3">📊</div>
            <h4 className="font-bold text-lg mb-2">만족도 5단계 분류</h4>
            <p className="text-gray-600 text-sm">
              통계 기반 IQR 경계값으로 정량적 만족도 분석
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-3">🔍</div>
            <h4 className="font-bold text-lg mb-2">이상치 탐지</h4>
            <p className="text-gray-600 text-sm">
              BoxPlot으로 극단적 의견과 스팸 리뷰 식별
            </p>
          </div>
          <div className="text-center">
            <div className="text-4xl mb-3">🤖</div>
            <h4 className="font-bold text-lg mb-2">LLM 해석 텍스트</h4>
            <p className="text-gray-600 text-sm">
              Google Gemini가 분포를 자연어로 해석
            </p>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-primary to-blue-600 rounded-xl shadow-xl p-8 text-white text-center">
        <h2 className="text-3xl font-bold mb-4">
          지금 바로 축제를 분석해보세요
        </h2>
        <p className="text-lg mb-6 opacity-90">
          카테고리 선택 또는 직접 검색으로 시작할 수 있습니다
        </p>
        <Link
          to="/search"
          className="inline-block bg-white text-primary px-8 py-3 rounded-lg text-lg font-semibold hover:bg-gray-100 transition"
        >
          축제 검색하기
        </Link>
      </div>
    </div>
  )
}
