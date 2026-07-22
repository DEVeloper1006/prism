import { useMemo } from "react";
import type { Clip } from "../lib/types";
import { API_URL } from "../lib/constants";

interface TimelineViewProps {
  clips: Clip[];
}

export default function TimelineView({ clips }: TimelineViewProps) {
  const sortedClips = useMemo(
    () => [...clips].sort((a, b) => (a.created_at || "").localeCompare(b.created_at || "")),
    [clips],
  );

  const maxDuration = useMemo(
    () => Math.max(...clips.map(c => c.duration_seconds || 0), 1),
    [clips],
  );

  if (clips.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-text-tertiary text-sm">No clips to display on timeline.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2 border-b border-border flex justify-between items-center">
        <span className="text-xs font-semibold text-text-primary">Timeline</span>
        <span className="text-xs text-text-secondary tabular-nums">{clips.length} clips</span>
      </div>

      <div className="flex-1 overflow-auto px-4 py-3">
        <div className="space-y-1">
          {sortedClips.map((clip) => {
            const widthPct = ((clip.duration_seconds || 0) / maxDuration) * 100;
            const qualityColor =
              (clip.sharpness_score ?? 0) >= 70 ? "bg-track-technical" :
              (clip.sharpness_score ?? 0) >= 40 ? "bg-track-face" :
              "bg-track-metadata";

            return (
              <div key={clip.id} className="flex items-center gap-2 group">
                <div className="w-32 shrink-0 truncate text-xs text-text-secondary">{clip.id}</div>
                <div className="flex-1 h-6 relative">
                  <div
                    className={`h-full rounded ${qualityColor}/60 group-hover:${qualityColor} transition-colors cursor-pointer`}
                    style={{ width: `${Math.max(widthPct, 2)}%` }}
                  >
                    <img
                      src={`${API_URL}/clips/${encodeURIComponent(clip.id)}/thumbnail`}
                      alt=""
                      className="h-full rounded object-cover opacity-80"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                    />
                  </div>
                </div>
                <div className="w-16 text-right text-xs text-text-tertiary tabular-nums shrink-0">
                  {clip.duration_seconds ? `${clip.duration_seconds.toFixed(1)}s` : "—"}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
