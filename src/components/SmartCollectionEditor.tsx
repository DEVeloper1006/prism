import { useState, useEffect } from "react";
import type { SmartCollection } from "../lib/types";
import { getCollections, createCollection } from "../lib/api";

interface SmartCollectionEditorProps {
  onSelectCollection?: (collectionId: number) => void;
}

export default function SmartCollectionEditor({ onSelectCollection }: SmartCollectionEditorProps) {
  const [collections, setCollections] = useState<SmartCollection[]>([]);
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [qualityMin, setQualityMin] = useState(0);
  const [shotType, setShotType] = useState("");

  useEffect(() => {
    getCollections().then(setCollections).catch(() => {});
  }, []);

  const handleCreate = async () => {
    const rules: Record<string, unknown> = {};
    if (qualityMin > 0) rules.quality_min = qualityMin;
    if (shotType) rules.shot_type = shotType;

    await createCollection(name, JSON.stringify(rules));
    setCreating(false);
    setName("");
    const updated = await getCollections();
    setCollections(updated);
  };

  return (
    <div className="p-3">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-xs font-semibold text-text-primary">Smart Collections</h3>
        <button onClick={() => setCreating(true)} className="text-xs text-interactive hover:underline">
          New
        </button>
      </div>

      {creating && (
        <div className="bg-surface rounded-lg p-3 mb-3 space-y-2">
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Collection name"
            className="w-full bg-panel border border-border rounded px-2 py-1 text-xs text-text-primary placeholder-text-tertiary"
          />
          <select
            value={shotType}
            onChange={(e) => setShotType(e.target.value)}
            className="w-full bg-panel border border-border rounded px-2 py-1 text-xs text-text-primary"
          >
            <option value="">Any shot type</option>
            <option value="close-up">Close-up</option>
            <option value="medium">Medium</option>
            <option value="wide">Wide</option>
          </select>
          <div className="flex gap-2">
            <button onClick={handleCreate} className="text-xs bg-interactive text-white rounded px-2 py-1">
              Create
            </button>
            <button onClick={() => setCreating(false)} className="text-xs text-text-secondary">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-1">
        {collections.map((coll) => (
          <button
            key={coll.id}
            onClick={() => onSelectCollection?.(coll.id)}
            className="w-full text-left px-2 py-1.5 rounded hover:bg-surface transition-colors text-xs text-text-primary"
          >
            {coll.name}
          </button>
        ))}
        {collections.length === 0 && !creating && (
          <p className="text-xs text-text-tertiary">No collections yet.</p>
        )}
      </div>
    </div>
  );
}
