import { useState, useEffect } from "react";

interface LUT {
  name: string;
  path: string;
}

interface LutSelectorProps {
  onSelect?: (lutName: string | null) => void;
}

export default function LutSelector({ onSelect }: LutSelectorProps) {
  const [luts, setLuts] = useState<LUT[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://127.0.0.1:8420/luts")
      .then(r => r.json())
      .then(setLuts)
      .catch(() => {});
  }, []);

  const handleChange = (value: string) => {
    const v = value || null;
    setSelected(v);
    onSelect?.(v);
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-text-tertiary">LUT:</span>
      <select
        value={selected || ""}
        onChange={(e) => handleChange(e.target.value)}
        className="bg-surface border border-border rounded px-2 py-0.5 text-xs text-text-primary"
      >
        <option value="">None</option>
        <option value="rec709">Rec.709</option>
        {luts.map((lut) => (
          <option key={lut.name} value={lut.name}>{lut.name}</option>
        ))}
      </select>
    </div>
  );
}
