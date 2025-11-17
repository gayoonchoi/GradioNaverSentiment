import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

interface AbsoluteScoreChartProps {
  scores: number[]
}

export default function AbsoluteScoreChart({ scores }: AbsoluteScoreChartProps) {
  if (!scores || scores.length === 0) {
    return <div className="text-center text-gray-500">데이터 없음</div>
  }

  // 고정된 구간으로 분류
  const bins = [
    { label: '매우 부정\n(<-2)', min: -Infinity, max: -2 },
    { label: '부정\n(-2~-1)', min: -2, max: -1 },
    { label: '약간 부정\n(-1~0)', min: -1, max: 0 },
    { label: '약간 긍정\n(0~1)', min: 0, max: 1 },
    { label: '긍정\n(1~2)', min: 1, max: 2 },
    { label: '매우 긍정\n(>2)', min: 2, max: Infinity },
  ]

  const data = bins.map((bin) => ({
    name: bin.label,
    count: scores.filter((s) => s >= bin.min && s < bin.max).length,
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ top: 20, right: 30, bottom: 20, left: 20 }}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" fontSize={11} />
        <YAxis />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="count"
          stroke="#1E90FF"
          strokeWidth={2}
          dot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
