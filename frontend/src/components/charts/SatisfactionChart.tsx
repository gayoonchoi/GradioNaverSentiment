import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import type { SatisfactionCounts } from '../../types'

interface SatisfactionChartProps {
  counts: SatisfactionCounts
}

const COLORS = {
  '매우 불만족': '#FF5733',
  '불만족': '#FF8C33',
  '보통': '#FFC300',
  '만족': '#A2D9A0',
  '매우 만족': '#4CAF50',
}

export default function SatisfactionChart({ counts }: SatisfactionChartProps) {
  const data = [
    { name: '매우 불만족', value: counts['매우 불만족'] || 0 },
    { name: '불만족', value: counts['불만족'] || 0 },
    { name: '보통', value: counts['보통'] || 0 },
    { name: '만족', value: counts['만족'] || 0 },
    { name: '매우 만족', value: counts['매우 만족'] || 0 },
  ]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="name"
          angle={-15}
          textAnchor="end"
          height={80}
          fontSize={12}
        />
        <YAxis />
        <Tooltip />
        <Bar dataKey="value" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={`cell-${index}`}
              fill={COLORS[entry.name as keyof typeof COLORS]}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
