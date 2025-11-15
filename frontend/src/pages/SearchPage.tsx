import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getCategories, getMediumCategories, getSmallCategories } from '../lib/api'
import { FaSearch } from 'react-icons/fa'

export default function SearchPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [selectedCat1, setSelectedCat1] = useState<string>('')
  const [selectedCat2, setSelectedCat2] = useState<string>('')
  const [selectedCat3, setSelectedCat3] = useState<string>('')
  const [keyword, setKeyword] = useState<string>('')
  const [numReviews, setNumReviews] = useState<number>(10)
  const [numReviewsCategory, setNumReviewsCategory] = useState<number>(10)

  // URL 파라미터에서 키워드 또는 카테고리 자동 입력
  useEffect(() => {
    const urlKeyword = searchParams.get('keyword')
    const urlCat1 = searchParams.get('cat1')
    const urlCat2 = searchParams.get('cat2')
    const urlCat3 = searchParams.get('cat3')

    if (urlKeyword) {
      setKeyword(decodeURIComponent(urlKeyword))
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }

    if (urlCat1) {
      setSelectedCat1(decodeURIComponent(urlCat1))
    }
    if (urlCat2) {
      setSelectedCat2(decodeURIComponent(urlCat2))
    }
    if (urlCat3) {
      setSelectedCat3(decodeURIComponent(urlCat3))
    }
  }, [searchParams])

  // 카테고리 데이터 fetch
  const { data: cat1Options = [] } = useQuery({
    queryKey: ['categories'],
    queryFn: getCategories,
  })

  const { data: cat2Options = [] } = useQuery({
    queryKey: ['categories', 'medium', selectedCat1],
    queryFn: () => getMediumCategories(selectedCat1),
    enabled: !!selectedCat1,
  })

  const { data: cat3Options = [] } = useQuery({
    queryKey: ['categories', 'small', selectedCat1, selectedCat2],
    queryFn: () => getSmallCategories(selectedCat1, selectedCat2),
    enabled: !!selectedCat1 && !!selectedCat2,
  })

  const handleDirectSearch = () => {
    if (!keyword.trim()) {
      alert('축제명을 입력해주세요')
      return
    }
    navigate(`/analysis/${encodeURIComponent(keyword)}?reviews=${numReviews}`)
  }

  const handleCategorySearch = () => {
    if (!selectedCat1 || !selectedCat2 || !selectedCat3) {
      alert('카테고리를 모두 선택해주세요')
      return
    }
    navigate(
      `/analysis/category?cat1=${selectedCat1}&cat2=${selectedCat2}&cat3=${selectedCat3}&reviews=${numReviewsCategory}`
    )
  }

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">축제 검색</h1>
        <p className="text-gray-600">
          축제명 직접 입력 또는 카테고리 선택으로 분석 시작
        </p>
      </div>

      {/* 직접 검색 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4 flex items-center">
          <FaSearch className="mr-2 text-primary" />
          직접 검색
        </h2>
        {searchParams.get('keyword') && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              💡 <strong>"{decodeURIComponent(searchParams.get('keyword')!)}"</strong> 축제가 자동으로 입력되었습니다.
              <br />
              후기 개수를 선택하고 <strong>분석 시작</strong> 버튼을 눌러주세요!
            </p>
          </div>
        )}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              축제명
            </label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="예: 강릉커피축제, 보령머드축제"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              onKeyPress={(e) => e.key === 'Enter' && handleDirectSearch()}
            />
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
            <div className="flex justify-between text-xs text-gray-500">
              <span>1개 (빠름)</span>
              <span>20개 (정밀)</span>
            </div>
          </div>
          <button
            onClick={handleDirectSearch}
            className="w-full bg-primary text-white py-3 rounded-lg font-semibold hover:bg-blue-600 transition"
          >
            분석 시작
          </button>
        </div>
      </div>

      {/* 카테고리 검색 */}
      <div className="bg-white rounded-xl shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">카테고리별 검색</h2>
        {(searchParams.get('cat1') || searchParams.get('cat2') || searchParams.get('cat3')) && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm text-green-800">
              💡 카테고리가 자동으로 선택되었습니다.
              <br />
              축제별 후기 개수를 선택하고 <strong>분석 시작</strong> 버튼을 눌러주세요!
            </p>
          </div>
        )}
        <div className="grid md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              대분류
            </label>
            <select
              value={selectedCat1}
              onChange={(e) => {
                setSelectedCat1(e.target.value)
                setSelectedCat2('')
                setSelectedCat3('')
              }}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary"
            >
              <option value="">선택하세요</option>
              {cat1Options.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              중분류
            </label>
            <select
              value={selectedCat2}
              onChange={(e) => {
                setSelectedCat2(e.target.value)
                setSelectedCat3('')
              }}
              disabled={!selectedCat1}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary disabled:bg-gray-100"
            >
              <option value="">선택하세요</option>
              {cat2Options.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              소분류
            </label>
            <select
              value={selectedCat3}
              onChange={(e) => setSelectedCat3(e.target.value)}
              disabled={!selectedCat2}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary disabled:bg-gray-100"
            >
              <option value="">선택하세요</option>
              {cat3Options.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            각 축제별 분석할 리뷰 수: {numReviewsCategory}개
          </label>
          <input
            type="range"
            min="1"
            max="20"
            value={numReviewsCategory}
            onChange={(e) => setNumReviewsCategory(Number(e.target.value))}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-gray-500">
            <span>1개 (빠름)</span>
            <span>20개 (정밀)</span>
          </div>
        </div>
        <button
          onClick={handleCategorySearch}
          disabled={!selectedCat1 || !selectedCat2 || !selectedCat3}
          className="w-full bg-green-500 text-white py-3 rounded-lg font-semibold hover:bg-green-600 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
        >
          카테고리 분석 시작
        </button>
      </div>
    </div>
  )
}
