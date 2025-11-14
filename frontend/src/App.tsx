import { Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import SearchPage from './pages/SearchPage'
import AnalysisPage from './pages/AnalysisPage'
import CategoryAnalysisPage from './pages/CategoryAnalysisPage'
import ComparisonPage from './pages/ComparisonPage'
import SeasonalTrendPage from './pages/SeasonalTrendPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="analysis/:keyword" element={<AnalysisPage />} />
        <Route path="analysis/category" element={<CategoryAnalysisPage />} />
        <Route path="comparison" element={<ComparisonPage />} />
        <Route path="seasonal" element={<SeasonalTrendPage />} />
      </Route>
    </Routes>
  )
}

export default App
