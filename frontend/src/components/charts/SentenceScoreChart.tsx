import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';
import ReactMarkdown from 'react-markdown';
import { BlogResult } from '../../types';

interface SentenceScoreChartProps {
  judgments: BlogResult['judgments'];
}

const SentenceScoreChart: React.FC<SentenceScoreChartProps> = ({ judgments }) => {
  // Chart data preparation
  const chartData = judgments.map((j, index) => ({
    id: index + 1, // 1-based sentence number for display
    sentence: j.sentence,
    score: j.score,
    verdict: j.final_verdict,
  }));

  // Calculate dynamic Y-axis domain
  const scores = chartData.map(d => d.score);
  const minScore = Math.min(...scores, 0); // Include 0
  const maxScore = Math.max(...scores, 0); // Include 0
  const yMin = Math.floor(minScore);
  const yMax = Math.ceil(maxScore);

  // Generate integer ticks including 0
  const generateTicks = () => {
    const ticks = [];
    for (let i = yMin; i <= yMax; i++) {
      ticks.push(i);
    }
    return ticks;
  };

  // Custom Tooltip to show full sentence
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="p-3 bg-white border border-gray-300 rounded shadow-lg max-w-sm">
          <p className="text-sm font-bold mb-1">문장 #{data.id}</p>
          <p className="text-sm"><span className="font-semibold">{data.verdict}</span> (점수: {data.score.toFixed(2)})</p>
          <p className="text-xs text-gray-700 mt-2 leading-relaxed">{data.sentence}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full">
      <div className="mb-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <h4 className="text-sm font-bold text-blue-900 mb-2">📊 차트 설명</h4>
        <ul className="text-xs text-blue-800 space-y-1">
          <li><strong>X축:</strong> 각 막대는 블로그 내 문장의 순서를 나타냅니다 (1번, 2번, 3번...)</li>
          <li><strong>Y축:</strong> 감성 점수를 나타냅니다 (양수 = 긍정, 음수 = 부정, 0 = 중립)</li>
          <li><strong>색상:</strong> 초록색은 긍정 문장, 빨간색은 부정 문장을 의미합니다</li>
          <li><strong>Tip:</strong> 막대 위에 마우스를 올리면 해당 문장의 전체 내용을 볼 수 있습니다</li>
        </ul>
      </div>
      <ResponsiveContainer width="100%" height={320}>
        <BarChart
          data={chartData}
          margin={{
            top: 20,
            right: 30,
            left: 40,
            bottom: 60,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="id"
            label={{ value: '문장 번호', position: 'insideBottom', offset: -10, style: { fontSize: 12, fontWeight: 'bold' } }}
            tick={{ fontSize: 10 }}
            interval={chartData.length > 20 ? 'preserveStartEnd' : 0}
          />
          <YAxis
            domain={[yMin, yMax]}
            ticks={generateTicks()}
            label={{ value: '감성 점수', angle: -90, position: 'insideLeft', style: { fontSize: 12, fontWeight: 'bold' } }}
            tick={{ fontSize: 11 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={0} stroke="#000" strokeWidth={2} strokeDasharray="3 3" label={{ value: '중립 (0점)', position: 'right', style: { fontSize: 10 } }} />
          <Bar dataKey="score" radius={[4, 4, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.score > 0 ? '#4CAF50' : entry.score < 0 ? '#F44336' : '#9E9E9E'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SentenceScoreChart;
