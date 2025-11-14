import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface DonutChartProps {
  positive: number
  negative: number
}

export default function DonutChart({ positive, negative }: DonutChartProps) {
  const total = positive + negative
  if (total === 0) {
    return <div className="text-center text-gray-500">데이터 없음</div>
  }

  const data = [
    { name: '긍정', value: positive, color: '#5463FF' },
    { name: '부정', value: negative, color: '#FF1818' },
  ]

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          fill="#8884d8"
          paddingAngle={5}
          dataKey="value"
          label={({ name, percent }) =>
            `${name} ${(percent * 100).toFixed(1)}%`
          }
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  )
}
