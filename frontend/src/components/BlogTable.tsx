import React, { useState } from 'react'
import { FaExternalLinkAlt, FaChevronLeft, FaChevronRight } from 'react-icons/fa'
import type { BlogResult, Judgment } from '../types'
import SentenceScoreChart from './charts/SentenceScoreChart'

// Helper component to parse and highlight sentences with '****' markers
const Highlight: React.FC<{ text: string; verdict: string }> = ({ text, verdict }) => {
  // Split by the marker, keeping the delimiters
  const parts = text.split(/(\*{4}.*?\*{4})/g).filter(Boolean);
  const isPositive = verdict === '긍정';

  return (
    <>
      {parts.map((part, index) => {
        if (part.startsWith('****') && part.endsWith('****')) {
          return (
            <strong
              key={index}
              className={isPositive ? 'text-green-600' : 'text-red-600'}
            >
              {part.slice(4, -4)}
            </strong>
          );
        }
        // Render non-highlighted parts as regular text
        return <span key={index}>{part}</span>;
      })}
    </>
  );
};


interface BlogTableProps {
  blogs: BlogResult[]
  pageSize?: number
}

export default function BlogTable({ blogs, pageSize = 5 }: BlogTableProps) {
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedBlogIndex, setSelectedBlogIndex] = useState<number | null>(null)
  const totalPages = Math.ceil(blogs.length / pageSize)

  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const currentBlogs = blogs.slice(startIndex, endIndex)

  const goToPage = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)))
    setSelectedBlogIndex(null);
  }

  const handleRowClick = (index: number) => {
    setSelectedBlogIndex(selectedBlogIndex === index ? null : index);
  }

  if (blogs.length === 0) {
    return (
      <div className="text-center text-gray-500 py-8">
        분석된 블로그가 없습니다
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 테이블 */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                블로그 제목
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                긍정
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                부정
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                비율
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                만족도
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {currentBlogs.map((blog, index) => (
              <React.Fragment key={startIndex + index}>
                <tr
                  className="hover:bg-gray-50 cursor-pointer"
                  onClick={() => handleRowClick(startIndex + index)}
                >
                  <td className="px-6 py-4 text-sm">
                    <a
                      href={blog['링크']}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline flex items-center space-x-2"
                      onClick={(e) => e.stopPropagation()}
                    >
                      <span className="truncate max-w-xs">
                        {blog['블로그 제목']}
                      </span>
                      <FaExternalLinkAlt className="flex-shrink-0" />
                    </a>
                  </td>
                  <td className="px-6 py-4 text-sm text-green-600 font-semibold">
                    {blog['긍정 문장 수']}
                  </td>
                  <td className="px-6 py-4 text-sm text-red-600 font-semibold">
                    {blog['부정 문장 수']}
                  </td>
                  <td className="px-6 py-4 text-sm">
                    <div className="flex items-center space-x-2">
                      <div className="w-24 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-500 h-2 rounded-full"
                          style={{
                            width: `${parseFloat(blog['긍정 비율 (%)']) || 0}%`,
                          }}
                        />
                      </div>
                      <span className="text-xs text-gray-600">
                        {blog['긍정 비율 (%)']}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm font-semibold">
                    {blog['평균 만족도'] || 'N/A'}
                  </td>
                </tr>
                {selectedBlogIndex === (startIndex + index) && (
                  <tr className="bg-gray-100">
                    <td colSpan={5} className="p-4">
                      <div className="space-y-4">
                        <h4 className="text-lg font-bold mb-2">문장별 감성 분석 상세</h4>
                        {blog.judgments && blog.judgments.length > 0 ? (
                          <>
                            <div className="space-y-2 text-sm">
                              {blog.judgments.map((judgment: Judgment, jIndex: number) => {
                                const isPositive = judgment.final_verdict === '긍정';
                                const verdictColor = isPositive ? 'text-green-600' : 'text-red-600';
                                // BE에서 넘어온 문장 앞의 '- ' 또는 '-' 제거
                                const cleanSentence = judgment.sentence.replace(/^- ?/, '').trim();

                                return (
                                  <p key={jIndex} className="text-gray-800">
                                    <span className={`font-semibold ${verdictColor}`}>
                                      [{judgment.final_verdict}({judgment.satisfaction_level || 'N/A'}점)]
                                    </span>
                                    <span className="ml-2">
                                      <Highlight text={cleanSentence} verdict={judgment.final_verdict} />
                                    </span>
                                  </p>
                                );
                              })}
                            </div>
                            <div className="mt-4">
                              <h5 className="text-md font-semibold mb-2">점수 분포 그래프</h5>
                              <SentenceScoreChart judgments={blog.judgments} />
                            </div>
                          </>
                        ) : (
                          <p className="text-gray-500">상세 분석 데이터가 없습니다.</p>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>

      {/* 페이지네이션 */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            총 {blogs.length}개 중 {startIndex + 1}-{Math.min(endIndex, blogs.length)}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => goToPage(currentPage - 1)}
              disabled={currentPage === 1}
              className="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FaChevronLeft />
            </button>
            <span className="text-sm text-gray-600">
              {currentPage} / {totalPages}
            </span>
            <button
              onClick={() => goToPage(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="px-3 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FaChevronRight />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
