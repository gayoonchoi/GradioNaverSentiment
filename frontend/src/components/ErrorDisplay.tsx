import { FaExclamationTriangle } from 'react-icons/fa'

interface ErrorDisplayProps {
  title?: string
  message: string
  onRetry?: () => void
}

export default function ErrorDisplay({
  title = '분석 실패',
  message,
  onRetry,
}: ErrorDisplayProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6">
      <div className="flex items-start space-x-3">
        <FaExclamationTriangle className="text-red-500 text-2xl flex-shrink-0 mt-1" />
        <div className="flex-1">
          <h2 className="text-xl font-bold text-red-800 mb-2">{title}</h2>
          <p className="text-red-600 mb-4">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition"
            >
              다시 시도
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
