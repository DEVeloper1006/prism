interface WaveformDisplayProps {
  data: number[];
  markers?: Array<{ timestamp: number; color: string }>;
  duration: number;
}

export default function WaveformDisplay({ data, markers = [], duration }: WaveformDisplayProps) {
  if (data.length === 0) return null;

  const max = Math.max(...data.map(Math.abs), 1);
  const width = 400;
  const height = 40;
  const barWidth = width / data.length;

  return (
    <div className="relative">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full" style={{ height: 40 }}>
        {data.map((val, i) => {
          const barHeight = (Math.abs(val) / max) * (height / 2);
          return (
            <rect
              key={i}
              x={i * barWidth}
              y={height / 2 - barHeight}
              width={Math.max(barWidth - 0.5, 0.5)}
              height={barHeight * 2}
              fill="#5AC8C8"
              opacity={0.7}
            />
          );
        })}
        {markers.map((m, i) => {
          const x = (m.timestamp / duration) * width;
          return (
            <circle key={i} cx={x} cy={height / 2} r={3} fill={m.color} />
          );
        })}
      </svg>
    </div>
  );
}
