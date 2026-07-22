import { useEffect, useState } from "react";
import type { Clip, Marker } from "../lib/types";
import ScoreBar from "./ScoreBar";
import ColorPalette from "./ColorPalette";
import { getMarkers, getClipPalette } from "../lib/api";
import { API_URL } from "../lib/constants";

interface ClipDetailProps {
  clip: Clip | null;
}

export default function ClipDetail({ clip }: ClipDetailProps) {
  const [markers, setMarkers] = useState<Marker[]>([]);
  const [palette, setPalette] = useState<string[]>([]);

  useEffect(() => {
    if (!clip) return;
    getMarkers(clip.id).then(setMarkers).catch(() => setMarkers([]));
    getClipPalette(clip.id).then(setPalette).catch(() => setPalette([]));
  }, [clip?.id]);

  if (!clip) {
    return (
      <aside className="w-72 bg-panel border-l border-border p-4 overflow-y-auto shrink-0">
        <p className="text-xs text-text-tertiary">Select a clip to view details.</p>
      </aside>
    );
  }

  const formatSize = (bytes: number | null) => {
    if (!bytes) return "—";
    if (bytes > 1e9) return `${(bytes / 1e9).toFixed(1)} GB`;
    if (bytes > 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    return `${(bytes / 1e3).toFixed(0)} KB`;
  };

  return (
    <aside className="w-72 bg-panel border-l border-border p-4 overflow-y-auto shrink-0">
      <div className="aspect-video bg-surface rounded-lg overflow-hidden mb-3">
        <img
          src={`${API_URL}/clips/${encodeURIComponent(clip.id)}/thumbnail`}
          alt={clip.id}
          className="w-full h-full object-cover"
          onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
        />
      </div>

      <h3 className="text-sm font-semibold text-text-primary mb-3 truncate">{clip.id}</h3>

      <Section title="Technical">
        <Row label="Resolution" value={clip.resolution} />
        <Row label="FPS" value={clip.fps?.toString()} />
        <Row label="Codec" value={clip.codec} />
        <Row label="Duration" value={clip.duration_seconds ? `${clip.duration_seconds.toFixed(1)}s` : undefined} />
        <Row label="Size" value={formatSize(clip.file_size_bytes)} />
        <Row label="Color Space" value={clip.color_space} />
        <Row label="Camera" value={clip.camera} />
      </Section>

      <Section title="Quality" color="text-track-technical">
        {clip.sharpness_score !== null && <ScoreBar score={clip.sharpness_score} label="Sharp" />}
        {clip.exposure_score !== null && <ScoreBar score={clip.exposure_score} label="Exposure" />}
        {clip.stability_score !== null && <ScoreBar score={clip.stability_score} label="Stable" />}
        {clip.color_score !== null && <ScoreBar score={clip.color_score} label="Color" />}
      </Section>

      {clip.scene_caption && (
        <Section title="Scene" color="text-track-visual">
          <p className="text-xs text-text-secondary leading-relaxed">{clip.scene_caption}</p>
        </Section>
      )}

      {clip.audio_quality && (
        <Section title="Audio" color="text-track-audio">
          <Row label="Quality" value={clip.audio_quality} />
          <Row label="Channels" value={clip.audio_channels?.toString()} />
          <Row label="Dialogue" value={clip.has_dialogue ? "Yes" : "No"} />
        </Section>
      )}

      {palette.length > 0 && (
        <Section title="Color Palette">
          <ColorPalette colors={palette} />
        </Section>
      )}

      {markers.length > 0 && (
        <Section title="Markers">
          {markers.map((m) => (
            <div key={m.id} className="flex items-center gap-2 text-xs py-0.5">
              <div className="w-2 h-2 rounded-full" style={{ background: m.color === "blue" ? "#0A84FF" : m.color }} />
              <span className="text-text-tertiary tabular-nums">{m.timestamp_seconds.toFixed(1)}s</span>
              <span className="text-text-secondary truncate">{m.note || "—"}</span>
            </div>
          ))}
        </Section>
      )}
    </aside>
  );
}

function Section({ title, color, children }: { title: string; color?: string; children: React.ReactNode }) {
  return (
    <div className="mb-3">
      <h4 className={`text-xs font-semibold mb-1.5 ${color || "text-text-secondary"}`}>{title}</h4>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value?: string | null }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-text-tertiary">{label}</span>
      <span className="text-text-secondary">{value || "—"}</span>
    </div>
  );
}
