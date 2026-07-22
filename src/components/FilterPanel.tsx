import { useState } from "react";
import type { SearchQuery, SearchFilters } from "../lib/types";

interface FilterPanelProps {
  onSearch: (query: SearchQuery) => void;
}

export default function FilterPanel({ onSearch }: FilterPanelProps) {
  const [open, setOpen] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({});

  const applyFilters = () => {
    const active: SearchFilters = {};
    if (filters.resolution) active.resolution = filters.resolution;
    if (filters.camera) active.camera = filters.camera;
    if (filters.quality_min) active.quality_min = filters.quality_min;
    if (filters.shot_type) active.shot_type = filters.shot_type;
    onSearch({ filters: Object.keys(active).length > 0 ? active : undefined });
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="px-3 py-1.5 text-xs text-text-secondary bg-surface border border-border rounded-lg hover:text-text-primary transition-colors"
      >
        Filters
      </button>
    );
  }

  return (
    <div className="absolute right-3 top-12 z-40 bg-panel border border-border rounded-lg p-4 shadow-xl w-64">
      <div className="flex justify-between items-center mb-3">
        <span className="text-xs font-semibold text-text-primary">Filters</span>
        <button onClick={() => setOpen(false)} className="text-text-tertiary text-xs hover:text-text-secondary">
          Close
        </button>
      </div>

      <label className="block mb-2">
        <span className="text-xs text-text-secondary">Resolution</span>
        <select
          value={filters.resolution || ""}
          onChange={(e) => setFilters({ ...filters, resolution: e.target.value || undefined })}
          className="w-full mt-1 bg-surface border border-border rounded px-2 py-1 text-xs text-text-primary"
        >
          <option value="">Any</option>
          <option value="3840x2160">4K (3840x2160)</option>
          <option value="1920x1080">1080p (1920x1080)</option>
          <option value="1280x720">720p (1280x720)</option>
        </select>
      </label>

      <label className="block mb-2">
        <span className="text-xs text-text-secondary">Shot Type</span>
        <select
          value={filters.shot_type || ""}
          onChange={(e) => setFilters({ ...filters, shot_type: e.target.value || undefined })}
          className="w-full mt-1 bg-surface border border-border rounded px-2 py-1 text-xs text-text-primary"
        >
          <option value="">Any</option>
          <option value="close-up">Close-up</option>
          <option value="medium">Medium</option>
          <option value="wide">Wide</option>
          <option value="establishing">Establishing</option>
        </select>
      </label>

      <label className="block mb-3">
        <span className="text-xs text-text-secondary">Min Quality</span>
        <input
          type="range"
          min={0}
          max={100}
          value={filters.quality_min || 0}
          onChange={(e) => setFilters({ ...filters, quality_min: Number(e.target.value) || undefined })}
          className="w-full mt-1"
        />
        <span className="text-xs text-text-tertiary tabular-nums">{filters.quality_min || 0}</span>
      </label>

      <div className="flex gap-2">
        <button
          onClick={applyFilters}
          className="flex-1 text-xs bg-interactive text-white rounded px-2 py-1.5 hover:bg-interactive/90"
        >
          Apply
        </button>
        <button
          onClick={() => { setFilters({}); onSearch({}); }}
          className="text-xs text-text-secondary hover:text-text-primary px-2 py-1.5"
        >
          Reset
        </button>
      </div>
    </div>
  );
}
