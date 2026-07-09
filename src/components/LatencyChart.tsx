import { LineChart, Line, ResponsiveContainer } from "recharts";

interface LatencyChartProps {
  data: { time: number; value: number }[];
}

export default function LatencyChart({ data }: LatencyChartProps) {
  return (
    <ResponsiveContainer width="100%" height={40}>
      <LineChart data={data}>
        <Line type="monotone" dataKey="value" stroke="#6C5CE7" strokeWidth={1.5} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
