interface ScoreBarProps {
  score: number;
  label?: string;
}

export default function ScoreBar({ score, label }: ScoreBarProps) {
  const color = score >= 70 ? "bg-good" : score >= 40 ? "bg-warning" : "bg-bad";

  return (
    <div className="flex items-center gap-1.5 flex-1">
      {label && <span className="text-xs text-gray-500 w-16">{label}</span>}
      <div className="flex-1 h-1.5 bg-surface rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs font-mono text-gray-400 w-6 text-right">{score}</span>
    </div>
  );
}
