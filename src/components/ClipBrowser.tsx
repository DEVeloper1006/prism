import SearchBar from "./SearchBar";
import FilterPanel from "./FilterPanel";
import FaceSidebar from "./FaceSidebar";
import ClipDetail from "./ClipDetail";
import ClipCard from "./ClipCard";
import type { Clip, SearchQuery } from "../lib/types";

interface ClipBrowserProps {
  clips: Clip[];
  loading: boolean;
  selectedClip: Clip | null;
  onSelectClip: (clip: Clip | null) => void;
  onSearch: (query: SearchQuery) => void;
  onLoadMore: () => void;
  onStartIngest: () => void;
}

export default function ClipBrowser({
  clips, loading, selectedClip, onSelectClip, onSearch, onLoadMore, onStartIngest,
}: ClipBrowserProps) {
  return (
    <div className="flex h-full">
      <FaceSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 p-3 border-b border-border relative">
          <SearchBar onSearch={onSearch} />
          <FilterPanel onSearch={onSearch} />
        </div>

        {clips.length === 0 && !loading ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <p className="text-text-tertiary text-sm mb-4">No clips loaded.</p>
            <button
              onClick={onStartIngest}
              className="text-interactive text-sm hover:underline"
            >
              Start Processing
            </button>
          </div>
        ) : (
          <div
            className="flex-1 overflow-auto p-3"
            onScroll={(e) => {
              const el = e.currentTarget;
              if (el.scrollHeight - el.scrollTop - el.clientHeight < 200) {
                onLoadMore();
              }
            }}
          >
            <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-3">
              {clips.map((clip) => (
                <ClipCard
                  key={clip.id}
                  clip={clip}
                  selected={selectedClip?.id === clip.id}
                  onClick={onSelectClip}
                />
              ))}
            </div>
            {loading && (
              <div className="text-center py-4 text-text-tertiary text-xs">Loading...</div>
            )}
          </div>
        )}
      </div>
      <ClipDetail clip={selectedClip} />
    </div>
  );
}
