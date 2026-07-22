interface ProgressOverlayProps {
  visible: boolean;
  progress: number;
  processed: number;
  total: number;
  currentClip: string | null;
  currentTrack: string | null;
}

const trackLabels: Record<string, { label: string; color: string }> = {
  "T1:visual": { label: "Visual Intelligence", color: "bg-track-visual" },
  "T2:audio": { label: "Audio Intelligence", color: "bg-track-audio" },
  "T3:technical": { label: "Technical Scoring", color: "bg-track-technical" },
  "T4:faces": { label: "Face Detection", color: "bg-track-face" },
  "T5:metadata": { label: "Metadata", color: "bg-track-metadata" },
};

export default function ProgressOverlay({
  visible, progress, processed, total, currentClip, currentTrack,
}: ProgressOverlayProps) {
  if (!visible) return null;

  const track = currentTrack ? trackLabels[currentTrack] : null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50">
      <div className="glass mx-4 mb-4 rounded-xl p-4 max-w-lg ml-auto">
        <div className="flex justify-between items-center mb-2">
          <span className="text-xs font-semibold text-text-primary">Ingesting</span>
          <span className="text-xs text-text-secondary tabular-nums">
            {processed} / {total}
          </span>
        </div>

        <div className="h-1.5 bg-surface rounded-full overflow-hidden mb-2">
          <div
            className="h-full bg-interactive rounded-full transition-all duration-300"
            style={{ width: `${progress * 100}%` }}
          />
        </div>

        <div className="flex justify-between text-xs">
          {currentClip && (
            <span className="text-text-tertiary truncate">{currentClip}</span>
          )}
          {track && (
            <span className="text-text-secondary flex items-center gap-1.5">
              <span className={`w-1.5 h-1.5 rounded-full ${track.color}`} />
              {track.label}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
