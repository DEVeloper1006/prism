import type { StoryboardCell } from "../lib/types";
import { API_URL } from "../lib/constants";
import ScoreBar from "./ScoreBar";

interface StoryboardCellProps {
  cell: StoryboardCell;
  index: number;
  onRemove: () => void;
}

export default function StoryboardCellComponent({ cell, index, onRemove }: StoryboardCellProps) {
  return (
    <div className="bg-surface rounded-lg overflow-hidden group">
      <div className="aspect-video bg-panel relative">
        <img
          src={`${API_URL}/clips/${encodeURIComponent(cell.clip_id)}/thumbnail`}
          alt={cell.clip_id}
          className="w-full h-full object-cover"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
        <div className="absolute top-2 left-2 bg-black/70 text-text-primary text-xs px-1.5 py-0.5 rounded tabular-nums">
          {cell.shot_number}
        </div>
        {cell.duration_seconds && (
          <div className="absolute bottom-2 right-2 bg-black/70 text-text-primary text-xs px-1.5 py-0.5 rounded tabular-nums">
            {cell.duration_seconds.toFixed(1)}s
          </div>
        )}
        <button
          onClick={onRemove}
          className="absolute top-2 right-2 bg-black/70 text-track-metadata text-xs px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity"
        >
          Remove
        </button>
      </div>
      <div className="p-3">
        <div className="text-xs text-text-primary font-semibold mb-1">{cell.clip_id}</div>
        {cell.description && (
          <p className="text-xs text-text-secondary leading-relaxed mb-2">{cell.description}</p>
        )}
        <div className="space-y-1">
          {cell.quality_scores.sharpness !== null && (
            <ScoreBar score={cell.quality_scores.sharpness} label="Sharp" />
          )}
          {cell.quality_scores.exposure !== null && (
            <ScoreBar score={cell.quality_scores.exposure} label="Expo" />
          )}
        </div>
        {cell.notes && (
          <p className="text-xs text-text-tertiary mt-2 italic">{cell.notes}</p>
        )}
      </div>
    </div>
  );
}
