import { useEffect, useState } from "react";
import type { Clip, TranscriptSegment } from "../lib/types";
import { getTranscript } from "../lib/api";

interface TranscriptViewProps {
  selectedClip: Clip | null;
}

export default function TranscriptView({ selectedClip }: TranscriptViewProps) {
  const [segments, setSegments] = useState<TranscriptSegment[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (!selectedClip) {
      setSegments([]);
      return;
    }
    setLoading(true);
    getTranscript(selectedClip.id)
      .then(setSegments)
      .catch(() => setSegments([]))
      .finally(() => setLoading(false));
  }, [selectedClip?.id]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  const filtered = search
    ? segments.filter(s => s.text.toLowerCase().includes(search.toLowerCase()))
    : segments;

  if (!selectedClip) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-text-tertiary text-sm">Select a clip in the Browser view to see its transcript.</p>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2 border-b border-border flex items-center gap-3">
        <span className="text-xs font-semibold text-text-primary">{selectedClip.id}</span>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search transcript..."
          className="flex-1 bg-surface border border-border rounded px-2 py-1 text-xs text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-interactive"
        />
      </div>

      <div className="flex-1 overflow-auto px-4 py-3">
        {loading && <p className="text-text-tertiary text-xs">Loading transcript...</p>}
        {!loading && filtered.length === 0 && (
          <p className="text-text-tertiary text-xs">
            {segments.length === 0 ? "No transcript available for this clip." : "No matches found."}
          </p>
        )}
        <div className="space-y-2">
          {filtered.map((seg) => (
            <div key={seg.id} className="flex gap-3 group hover:bg-surface/50 rounded px-2 py-1 -mx-2 cursor-pointer transition-colors">
              <span className="text-xs text-track-audio tabular-nums shrink-0 w-12 pt-0.5">
                {formatTime(seg.start_time)}
              </span>
              <div className="flex-1">
                {seg.speaker_label && (
                  <span className="text-xs text-track-audio font-semibold mr-2">{seg.speaker_label}</span>
                )}
                <span className="text-sm text-text-primary leading-relaxed">{seg.text}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
