import { useState, useEffect } from "react";
import { getDailies } from "../lib/api";

interface DailiesData {
  date: string;
  total_clips: number;
  total_duration_seconds: number;
  cameras: Record<string, number>;
  quality_distribution: { good: number; warning: number; poor: number };
  top_clips: Array<Record<string, unknown>>;
}

export default function DailiesReport() {
  const [date, setDate] = useState(new Date().toISOString().split("T")[0]);
  const [data, setData] = useState<DailiesData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    getDailies(date)
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [date]);

  const formatDuration = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return h > 0 ? `${h}h ${m}m` : `${m}m`;
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-sm font-semibold text-text-primary">Dailies Report</h2>
        <input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="bg-surface border border-border rounded px-2 py-1 text-xs text-text-primary"
        />
      </div>

      {loading && <p className="text-text-tertiary text-xs">Loading...</p>}
      {data && !loading && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <Stat label="Total Clips" value={data.total_clips.toString()} />
            <Stat label="Total Duration" value={formatDuration(data.total_duration_seconds)} />
            <Stat label="Cameras" value={Object.keys(data.cameras).length.toString()} />
          </div>

          <div>
            <h4 className="text-xs font-semibold text-text-secondary mb-2">Quality Distribution</h4>
            <div className="flex gap-2">
              <QualityBar label="Good" count={data.quality_distribution.good} color="bg-track-technical" />
              <QualityBar label="Warning" count={data.quality_distribution.warning} color="bg-track-face" />
              <QualityBar label="Poor" count={data.quality_distribution.poor} color="bg-track-metadata" />
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-text-secondary mb-2">Cameras</h4>
            {Object.entries(data.cameras).map(([cam, count]) => (
              <div key={cam} className="flex justify-between text-xs py-0.5">
                <span className="text-text-primary">{cam}</span>
                <span className="text-text-tertiary tabular-nums">{count} clips</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-surface rounded-lg p-3 text-center">
      <div className="text-lg font-semibold text-text-primary tabular-nums">{value}</div>
      <div className="text-xs text-text-tertiary">{label}</div>
    </div>
  );
}

function QualityBar({ label, count, color }: { label: string; count: number; color: string }) {
  return (
    <div className="flex-1 text-center">
      <div className={`h-2 rounded-full ${color} mb-1`} />
      <div className="text-xs text-text-primary tabular-nums">{count}</div>
      <div className="text-xs text-text-tertiary">{label}</div>
    </div>
  );
}
