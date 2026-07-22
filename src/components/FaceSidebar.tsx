import { useEffect, useState } from "react";
import type { FaceCluster } from "../lib/types";
import { getFaces } from "../lib/api";

interface FaceSidebarProps {
  onSelectFace?: (clusterId: number) => void;
}

export default function FaceSidebar({ onSelectFace }: FaceSidebarProps) {
  const [clusters, setClusters] = useState<FaceCluster[]>([]);

  useEffect(() => {
    getFaces().then(setClusters).catch(() => {});
  }, []);

  return (
    <aside className="w-48 bg-panel border-r border-border p-3 overflow-y-auto shrink-0">
      <h3 className="text-xs font-semibold text-track-face mb-3">Faces</h3>
      {clusters.length === 0 ? (
        <p className="text-xs text-text-tertiary">No face clusters detected.</p>
      ) : (
        <div className="space-y-2">
          {clusters.map((cluster) => (
            <button
              key={cluster.id}
              onClick={() => onSelectFace?.(cluster.id)}
              className="w-full flex items-center gap-2 p-1.5 rounded hover:bg-surface transition-colors text-left"
            >
              <div className="w-8 h-8 rounded-full bg-surface border border-track-face/30 flex items-center justify-center text-xs text-track-face">
                {cluster.label?.charAt(0) || "?"}
              </div>
              <div>
                <div className="text-xs text-text-primary">{cluster.label || `Person ${cluster.id}`}</div>
                <div className="text-xs text-text-tertiary">{cluster.count} clips</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </aside>
  );
}
