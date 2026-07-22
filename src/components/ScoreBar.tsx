interface ScoreBarProps {
  score: number;
  label?: string;
}

export default function ScoreBar({ score, label }: ScoreBarProps) {
  const color =
    score >= 70 ? "bg-track-technical" :
    score >= 40 ? "bg-track-face" :
    "bg-track-metadata";

  return (
    <div className="flex items-center gap-1.5 flex-1">
      {label && <span className="text-xs text-text-secondary w-16">{label}</span>}
      <div className="flex-1 h-1 bg-surface rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-xs text-text-tertiary w-6 text-right tabular-nums">{score}</span>
    </div>
  );
}
