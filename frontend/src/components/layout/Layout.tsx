import { Outlet, Link } from 'react-router-dom'
import { FaChartBar, FaHome, FaSearch, FaCloudSun } from 'react-icons/fa'

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2">
              <FaChartBar className="text-primary text-2xl" />
              <span className="text-xl font-bold text-gray-900">
                FestInsight
              </span>
              <span className="text-sm text-gray-500 hidden md:inline">
                축제 기획자를 위한 감성 분석 플랫폼
              </span>
            </Link>

            <div className="flex items-center space-x-6">
              <Link
                to="/"
                className="flex items-center space-x-1 text-gray-700 hover:text-primary transition"
              >
                <FaHome />
                <span className="hidden sm:inline">홈</span>
              </Link>
              <Link
                to="/search"
                className="flex items-center space-x-1 text-gray-700 hover:text-primary transition"
              >
                <FaSearch />
                <span className="hidden sm:inline">검색</span>
              </Link>
              <Link
                to="/seasonal"
                className="flex items-center space-x-1 text-gray-700 hover:text-primary transition"
              >
                <FaCloudSun />
                <span className="hidden sm:inline">계절별</span>
              </Link>
              <Link
                to="/comparison"
                className="flex items-center space-x-1 text-gray-700 hover:text-primary transition"
              >
                <FaChartBar />
                <span className="hidden sm:inline">비교</span>
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-gray-500 text-sm">
            <p>© 2025 FestInsight. 네이버 블로그 리뷰 기반 축제 감성 분석 서비스</p>
            <p className="mt-2">
              Powered by Google Gemini LLM & LangGraph Multi-Agent System
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
