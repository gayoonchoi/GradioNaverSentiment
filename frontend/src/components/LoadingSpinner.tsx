import { FaSpinner } from 'react-icons/fa'

interface LoadingSpinnerProps {
  message?: string
  subtitle?: string
}

export default function LoadingSpinner({
  message = '분석 중...',
  subtitle,
}: LoadingSpinnerProps) {
  return (
    <div className="flex items-center justify-center min-h-[400px]">
      <div className="text-center">
        <FaSpinner className="animate-spin text-6xl text-primary mx-auto mb-4" />
        <p className="text-xl text-gray-600">{message}</p>
        {subtitle && (
          <p className="text-sm text-gray-500 mt-2">{subtitle}</p>
        )}
      </div>
    </div>
  )
}
