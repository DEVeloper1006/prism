import { useState, useCallback } from "react";
import type { Clip } from "../lib/types";
import { API_URL } from "../lib/constants";
import { exportFcpxml, exportEdl } from "../lib/api";

interface AssemblyWorkspaceProps {
  clips: Clip[];
}

interface AssemblySlot {
  clip: Clip;
  description: string;
}

export default function AssemblyWorkspace({ clips }: AssemblyWorkspaceProps) {
  const [assembly, setAssembly] = useState<AssemblySlot[]>([]);
  const [exporting, setExporting] = useState(false);

  const addToAssembly = useCallback((clip: Clip) => {
    setAssembly(prev => [...prev, { clip, description: clip.scene_caption || "" }]);
  }, []);

  const removeFromAssembly = useCallback((index: number) => {
    setAssembly(prev => prev.filter((_, i) => i !== index));
  }, []);

  const moveSlot = useCallback((from: number, to: number) => {
    setAssembly(prev => {
      const next = [...prev];
      const [moved] = next.splice(from, 1);
      next.splice(to, 0, moved);
      return next;
    });
  }, []);

  const handleExportFcpxml = useCallback(async () => {
    setExporting(true);
    try {
      const xml = await exportFcpxml(assembly.map(s => s.clip.id));
      const blob = new Blob([xml], { type: "application/xml" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "prism_assembly.fcpxml";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }, [assembly]);

  const handleExportEdl = useCallback(async () => {
    setExporting(true);
    try {
      const edl = await exportEdl(assembly.map(s => s.clip.id));
      const blob = new Blob([edl], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "prism_assembly.edl";
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }, [assembly]);

  const totalDuration = assembly.reduce((sum, s) => sum + (s.clip.duration_seconds || 0), 0);

  return (
    <div className="h-full flex">
      <div className="w-64 bg-panel border-r border-border overflow-y-auto p-3 shrink-0">
        <h3 className="text-xs font-semibold text-text-primary mb-2">Available Clips</h3>
        <div className="space-y-1">
          {clips.map((clip) => (
            <button
              key={clip.id}
              onClick={() => addToAssembly(clip)}
              className="w-full text-left flex items-center gap-2 p-1.5 rounded hover:bg-surface transition-colors"
            >
              <div className="w-12 h-8 bg-surface rounded overflow-hidden shrink-0">
                <img
                  src={`${API_URL}/clips/${encodeURIComponent(clip.id)}/thumbnail`}
                  alt=""
                  className="w-full h-full object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
              <div className="min-w-0">
                <div className="text-xs text-text-primary truncate">{clip.id}</div>
                <div className="text-xs text-text-tertiary tabular-nums">
                  {clip.duration_seconds ? `${clip.duration_seconds.toFixed(1)}s` : "—"}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="px-4 py-2 border-b border-border flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-text-primary">Assembly</span>
            <span className="text-xs text-text-secondary tabular-nums">
              {assembly.length} shots &middot; {totalDuration.toFixed(1)}s
            </span>
          </div>
          {assembly.length > 0 && (
            <div className="flex gap-2">
              <button
                onClick={handleExportFcpxml}
                disabled={exporting}
                className="text-xs text-interactive hover:underline disabled:opacity-50"
              >
                Export FCPXML
              </button>
              <button
                onClick={handleExportEdl}
                disabled={exporting}
                className="text-xs text-interactive hover:underline disabled:opacity-50"
              >
                Export EDL
              </button>
            </div>
          )}
        </div>

        <div className="flex-1 overflow-auto p-4">
          {assembly.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-text-tertiary text-sm">Click clips on the left to build your assembly.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {assembly.map((slot, i) => (
                <div key={`${slot.clip.id}-${i}`} className="flex items-center gap-3 bg-surface rounded-lg p-2 group">
                  <span className="text-xs text-text-tertiary w-6 tabular-nums">{i + 1}</span>
                  <div className="w-20 h-12 bg-panel rounded overflow-hidden shrink-0">
                    <img
                      src={`${API_URL}/clips/${encodeURIComponent(slot.clip.id)}/thumbnail`}
                      alt=""
                      className="w-full h-full object-cover"
                      onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                    />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs text-text-primary">{slot.clip.id}</div>
                    <div className="text-xs text-text-tertiary truncate">{slot.description || "—"}</div>
                  </div>
                  <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {i > 0 && (
                      <button onClick={() => moveSlot(i, i - 1)} className="text-text-tertiary hover:text-text-primary text-xs px-1">
                        Up
                      </button>
                    )}
                    {i < assembly.length - 1 && (
                      <button onClick={() => moveSlot(i, i + 1)} className="text-text-tertiary hover:text-text-primary text-xs px-1">
                        Dn
                      </button>
                    )}
                    <button onClick={() => removeFromAssembly(i)} className="text-track-metadata hover:text-track-metadata/80 text-xs px-1">
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
