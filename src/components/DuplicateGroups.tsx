import { useState, useEffect } from "react";
import type { DuplicateGroup } from "../lib/types";
import { getDuplicates } from "../lib/api";
import { API_URL } from "../lib/constants";

export default function DuplicateGroups() {
  const [groups, setGroups] = useState<DuplicateGroup[]>([]);

  useEffect(() => {
    getDuplicates().then(setGroups).catch(() => {});
  }, []);

  if (groups.length === 0) {
    return (
      <div className="p-4">
        <p className="text-xs text-text-tertiary">No duplicate groups found.</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-xs font-semibold text-text-primary">Duplicate Groups</h3>
      {groups.map((group) => (
        <div key={group.group_id} className="bg-surface rounded-lg p-3">
          <div className="text-xs text-text-secondary mb-2">{group.clips.length} similar clips</div>
          <div className="flex gap-2 overflow-x-auto">
            {group.clips.map((clip) => (
              <div
                key={clip.id}
                className={`shrink-0 w-32 rounded overflow-hidden ${
                  clip.id === group.best_clip_id ? "ring-2 ring-track-technical" : ""
                }`}
              >
                <div className="aspect-video bg-panel">
                  <img
                    src={`${API_URL}/clips/${encodeURIComponent(clip.id)}/thumbnail`}
                    alt=""
                    className="w-full h-full object-cover"
                    onError={(e) => { (e.target as HTMLImageElement).style.display = "none"; }}
                  />
                </div>
                <div className="p-1 text-center">
                  <div className="text-xs text-text-primary truncate">{clip.id}</div>
                  {clip.id === group.best_clip_id && (
                    <div className="text-xs text-track-technical">Best</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
