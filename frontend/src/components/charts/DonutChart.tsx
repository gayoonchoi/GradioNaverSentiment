import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'

interface DonutChartProps {
  positive: number
  negative: number
}

const RADIAN = Math.PI / 180;

const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  outerRadius,
  percent,
  name,
}: any) => {
  const radius = outerRadius + 30; // Place label outside the pie
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill="#374151"
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      className="text-sm font-semibold"
    >
      {`${name} ${(percent * 100).toFixed(1)}%`}
    </text>
  );
};

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
      <PieChart margin={{ top: 20, right: 60, bottom: 20, left: 60 }}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={50}
          outerRadius={80}
          fill="#8884d8"
          paddingAngle={5}
          dataKey="value"
          label={renderCustomizedLabel}
          labelLine={true}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.color} />
          ))}
        </Pie>
        <Tooltip />
        <Legend wrapperStyle={{ paddingTop: '10px' }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
