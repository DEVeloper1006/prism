import { useState, useCallback } from "react";
import type { Clip, StoryboardCell } from "../lib/types";
import { useStoryboard } from "../hooks/useStoryboard";
import StoryboardCellComponent from "./StoryboardCell";
import { API_URL } from "../lib/constants";

interface StoryboardViewProps {
  clips: Clip[];
}

export default function StoryboardView({ clips }: StoryboardViewProps) {
  const { storyboard, cells, loading, create, save, reorderCell, removeCell, addCell } = useStoryboard();
  const [newName, setNewName] = useState("");
  const [mode, setMode] = useState<"post_shoot" | "assembly">("post_shoot");

  const handleCreate = useCallback(async () => {
    if (!newName.trim()) return;
    await create(newName.trim(), mode);
    setNewName("");
  }, [newName, mode, create]);

  const handleAddClip = useCallback((clip: Clip) => {
    addCell({
      clip_id: clip.id,
      shot_number: cells.length + 1,
      description: clip.scene_caption || "",
      notes: "",
      keyframe_path: null,
      duration_seconds: clip.duration_seconds,
      quality_scores: {
        sharpness: clip.sharpness_score,
        exposure: clip.exposure_score,
        stability: clip.stability_score,
      },
    });
  }, [cells.length, addCell]);

  if (!storyboard) {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <div className="w-80">
          <h3 className="text-sm font-semibold text-text-primary mb-4 text-center">Create Storyboard</h3>
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Storyboard name..."
            className="w-full bg-surface border border-border rounded-lg px-3 py-2 text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-interactive mb-3"
          />
          <div className="flex gap-2 mb-4">
            <button
              onClick={() => setMode("post_shoot")}
              className={`flex-1 text-xs py-1.5 rounded-lg transition-colors ${
                mode === "post_shoot" ? "bg-interactive text-white" : "bg-surface text-text-secondary"
              }`}
            >
              Post-Shoot Board
            </button>
            <button
              onClick={() => setMode("assembly")}
              className={`flex-1 text-xs py-1.5 rounded-lg transition-colors ${
                mode === "assembly" ? "bg-interactive text-white" : "bg-surface text-text-secondary"
              }`}
            >
              Assembly Board
            </button>
          </div>
          <button
            onClick={handleCreate}
            disabled={!newName.trim()}
            className="w-full bg-interactive text-white text-sm py-2 rounded-lg hover:bg-interactive/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Create
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex">
      <div className="w-48 bg-panel border-r border-border overflow-y-auto p-3 shrink-0">
        <h3 className="text-xs font-semibold text-text-primary mb-2">Add Clips</h3>
        <div className="space-y-1">
          {clips.map((clip) => (
            <button
              key={clip.id}
              onClick={() => handleAddClip(clip)}
              className="w-full text-left p-1.5 rounded hover:bg-surface transition-colors"
            >
              <div className="w-full aspect-video bg-surface rounded overflow-hidden mb-1">
                <img
                  src={`${API_URL}/clips/${encodeURIComponent(clip.id)}/thumbnail`}
                  alt=""
                  className="w-full h-full object-cover"
                  onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                />
              </div>
              <div className="text-xs text-text-primary truncate">{clip.id}</div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 flex flex-col">
        <div className="px-4 py-2 border-b border-border flex justify-between items-center">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-text-primary">{storyboard.name}</span>
            <span className="text-xs text-text-secondary">{storyboard.mode === "post_shoot" ? "Post-Shoot" : "Assembly"}</span>
            <span className="text-xs text-text-tertiary">{cells.length} cells</span>
          </div>
          <button
            onClick={save}
            className="text-xs text-interactive hover:underline"
          >
            Save
          </button>
        </div>

        <div className="flex-1 overflow-auto p-4">
          {cells.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-text-tertiary text-sm">Add clips from the sidebar to build your storyboard.</p>
            </div>
          ) : (
            <div className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-4">
              {cells.map((cell, i) => (
                <StoryboardCellComponent
                  key={`${cell.clip_id}-${i}`}
                  cell={cell}
                  index={i}
                  onRemove={() => removeCell(i)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
