import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import ReactMarkdown from 'react-markdown';
import { BlogResult } from '../../types';

interface SentenceScoreChartProps {
  judgments: BlogResult['judgments'];
}

const SentenceScoreChart: React.FC<SentenceScoreChartProps> = ({ judgments }) => {
  // Filter out neutral sentences for the chart, or include them with score 0
  const chartData = judgments.map((j, index) => ({
    id: index, // Use index as a unique ID for each bar
    sentence: j.sentence,
    score: j.score,
    verdict: j.final_verdict,
  }));

  // Custom Tooltip to show full sentence
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="p-2 bg-white border border-gray-300 rounded shadow-md max-w-xs">
          <p className="text-sm font-bold">{data.verdict} ({data.score.toFixed(2)})</p>
          <p className="text-xs text-gray-700 mt-1">{data.sentence}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="id" hide /> {/* Hide XAxis labels, use tooltip for details */}
          <YAxis domain={[-5, 5]} /> {/* Assuming scores range from -5 to 5 */}
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="score" fill="#8884d8">
            {chartData.map((entry, index) => (
              <Bar
                key={`bar-${index}`}
                dataKey="score"
                fill={entry.score > 0 ? '#4CAF50' : '#F44336'} // Green for positive, Red for negative
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default SentenceScoreChart;
