import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'

interface OutlierChartProps {
  scores: number[]
}

export default function OutlierChart({ scores }: OutlierChartProps) {
  if (!scores || scores.length === 0) {
    return <div className="text-center text-gray-500">데이터 없음</div>
  }

  // IQR 계산
  const sortedScores = [...scores].sort((a, b) => a - b)
  const q1Index = Math.floor(sortedScores.length * 0.25)
  const q3Index = Math.floor(sortedScores.length * 0.75)
  const q1 = sortedScores[q1Index]
  const q3 = sortedScores[q3Index]
  const iqr = q3 - q1
  const lowerBound = q1 - 1.5 * iqr
  const upperBound = q3 + 1.5 * iqr
  const median = sortedScores[Math.floor(sortedScores.length / 2)]

  // 데이터 포인트 생성
  const data = scores.map((score, index) => ({
    x: 0,
    y: score,
    isOutlier: score < lowerBound || score > upperBound,
  }))

  return (
    <div>
      <ResponsiveContainer width="100%" height={250}>
        <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" dataKey="x" hide />
          <YAxis
            type="number"
            dataKey="y"
            domain={['dataMin - 0.5', 'dataMax + 0.5']}
          />
          <Tooltip
            cursor={{ strokeDasharray: '3 3' }}
            content={({ payload }) => {
              if (payload && payload.length > 0) {
                const point = payload[0].payload
                return (
                  <div className="bg-white p-2 border rounded shadow">
                    <p className="text-sm">
                      점수: {point.y.toFixed(2)}
                      {point.isOutlier && (
                        <span className="text-red-500 ml-2">(이상치)</span>
                      )}
                    </p>
                  </div>
                )
              }
              return null
            }}
          />
          <ReferenceLine
            y={q1}
            stroke="#888"
            strokeDasharray="3 3"
            label={{ value: 'Q1', position: 'right' }}
          />
          <ReferenceLine
            y={median}
            stroke="red"
            strokeWidth={2}
            label={{ value: 'Median', position: 'right' }}
          />
          <ReferenceLine
            y={q3}
            stroke="#888"
            strokeDasharray="3 3"
            label={{ value: 'Q3', position: 'right' }}
          />
          <ReferenceLine
            y={lowerBound}
            stroke="orange"
            strokeDasharray="5 5"
            label={{ value: 'Lower', position: 'right' }}
          />
          <ReferenceLine
            y={upperBound}
            stroke="orange"
            strokeDasharray="5 5"
            label={{ value: 'Upper', position: 'right' }}
          />
          <Scatter
            data={data.filter((d) => !d.isOutlier)}
            fill="lightblue"
            shape="circle"
          />
          <Scatter
            data={data.filter((d) => d.isOutlier)}
            fill="red"
            shape="circle"
          />
        </ScatterChart>
      </ResponsiveContainer>
      <div className="text-xs text-gray-600 mt-2 grid grid-cols-2 gap-2">
        <div>Q1: {q1.toFixed(2)}</div>
        <div>Q3: {q3.toFixed(2)}</div>
        <div>Median: {median.toFixed(2)}</div>
        <div>IQR: {iqr.toFixed(2)}</div>
      </div>
    </div>
  )
}
