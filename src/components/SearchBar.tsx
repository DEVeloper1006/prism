import { useState, useCallback } from "react";
import type { SearchQuery } from "../lib/types";

interface SearchBarProps {
  onSearch: (query: SearchQuery) => void;
}

export default function SearchBar({ onSearch }: SearchBarProps) {
  const [value, setValue] = useState("");

  const handleSubmit = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    onSearch({ query: value || undefined, top_k: 50 });
  }, [value, onSearch]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      setValue("");
      onSearch({});
    }
  }, [onSearch]);

  return (
    <form onSubmit={handleSubmit} className="flex-1 relative">
      <input
        type="text"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Search clips with natural language..."
        className="w-full bg-surface border border-border rounded-lg px-3 py-1.5 text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-interactive"
      />
      {value && (
        <button
          type="button"
          onClick={() => { setValue(""); onSearch({}); }}
          className="absolute right-8 top-1/2 -translate-y-1/2 text-text-tertiary text-xs hover:text-text-secondary"
        >
          Clear
        </button>
      )}
      <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-track-visual bg-track-visual/10 px-1.5 py-0.5 rounded">
        AI
      </span>
    </form>
  );
}
