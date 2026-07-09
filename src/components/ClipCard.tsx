import type { Clip } from "../lib/types";
import ScoreBar from "./ScoreBar";

interface ClipCardProps {
  clip: Clip;
  onClick: (clip: Clip) => void;
}

export default function ClipCard({ clip, onClick }: ClipCardProps) {
  return (
    <div
      onClick={() => onClick(clip)}
      className="bg-surface rounded-lg overflow-hidden cursor-pointer hover:ring-1 hover:ring-accent transition-all"
    >
      <div className="aspect-video bg-panel" />
      <div className="p-2">
        <p className="text-xs font-mono text-gray-300 truncate">{clip.id}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-gray-500">{clip.resolution}</span>
          <ScoreBar score={clip.sharpness_score ?? 0} />
        </div>
      </div>
    </div>
  );
}
