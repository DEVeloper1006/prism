import { useState } from "react";
import { createMarker } from "../lib/api";

interface MarkerPopoverProps {
  clipId: string;
  timestampSeconds: number;
  onCreated: () => void;
  onClose: () => void;
}

const COLORS = [
  { name: "Red", value: "#FF3B30" },
  { name: "Orange", value: "#FF9500" },
  { name: "Yellow", value: "#FFCC00" },
  { name: "Green", value: "#34C759" },
  { name: "Blue", value: "#0A84FF" },
  { name: "Purple", value: "#AF52DE" },
];

export default function MarkerPopover({ clipId, timestampSeconds, onCreated, onClose }: MarkerPopoverProps) {
  const [note, setNote] = useState("");
  const [color, setColor] = useState("#0A84FF");

  const handleCreate = async () => {
    await createMarker(clipId, timestampSeconds, note || undefined, color);
    onCreated();
    onClose();
  };

  return (
    <div className="glass rounded-lg p-3 w-64 shadow-xl">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-semibold text-text-primary">Add Marker</span>
        <span className="text-xs text-text-tertiary tabular-nums">{timestampSeconds.toFixed(1)}s</span>
      </div>
      <input
        type="text"
        value={note}
        onChange={(e) => setNote(e.target.value)}
        placeholder="Note..."
        className="w-full bg-surface border border-border rounded px-2 py-1 text-xs text-text-primary placeholder-text-tertiary mb-2"
        autoFocus
      />
      <div className="flex gap-1.5 mb-3">
        {COLORS.map((c) => (
          <button
            key={c.value}
            onClick={() => setColor(c.value)}
            className={`w-5 h-5 rounded-full transition-transform ${color === c.value ? "scale-125 ring-1 ring-white" : ""}`}
            style={{ backgroundColor: c.value }}
            title={c.name}
          />
        ))}
      </div>
      <div className="flex gap-2">
        <button onClick={handleCreate} className="flex-1 text-xs bg-interactive text-white rounded px-2 py-1">
          Add
        </button>
        <button onClick={onClose} className="text-xs text-text-secondary px-2 py-1">
          Cancel
        </button>
      </div>
    </div>
  );
}
