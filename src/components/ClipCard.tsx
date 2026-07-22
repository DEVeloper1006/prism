import { useState, useCallback } from "react";
import type { Clip } from "../lib/types";
import ScoreBar from "./ScoreBar";
import { API_URL } from "../lib/constants";

interface ClipCardProps {
  clip: Clip;
  selected: boolean;
  onClick: (clip: Clip) => void;
}

export default function ClipCard({ clip, selected, onClick }: ClipCardProps) {
  const [imgError, setImgError] = useState(false);
  const thumbUrl = `${API_URL}/clips/${encodeURIComponent(clip.id)}/thumbnail`;

  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "--:--";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div
      onClick={() => onClick(clip)}
      className={`rounded-lg overflow-hidden cursor-pointer transition-all ${
        selected
          ? "ring-2 ring-interactive"
          : "hover:ring-1 hover:ring-border"
      }`}
    >
      <div className="aspect-video bg-panel relative">
        {!imgError ? (
          <img
            src={thumbUrl}
            alt={clip.id}
            loading="lazy"
            className="w-full h-full object-cover"
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-text-tertiary text-xs">
            No thumbnail
          </div>
        )}
        <div className="absolute bottom-1 right-1 bg-black/70 text-text-primary text-xs px-1 rounded tabular-nums">
          {formatDuration(clip.duration_seconds)}
        </div>
        {clip.shot_type && (
          <div className="absolute top-1 left-1 bg-black/70 text-text-secondary text-xs px-1 rounded">
            {clip.shot_type}
          </div>
        )}
      </div>
      <div className="bg-surface p-2">
        <p className="text-xs text-text-primary truncate">{clip.id}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-text-tertiary">{clip.resolution}</span>
          {clip.sharpness_score !== null && (
            <ScoreBar score={clip.sharpness_score} />
          )}
        </div>
      </div>
    </div>
  );
}
