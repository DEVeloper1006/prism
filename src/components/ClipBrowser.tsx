import SearchBar from "./SearchBar";
import FilterPanel from "./FilterPanel";
import FaceSidebar from "./FaceSidebar";
import ClipDetail from "./ClipDetail";

export default function ClipBrowser() {
  return (
    <div className="flex h-full">
      <FaceSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <div className="flex items-center gap-2 p-3 border-b border-surface">
          <SearchBar />
          <FilterPanel />
        </div>
        <div className="flex-1 overflow-auto p-3">
          <p className="text-gray-500 text-sm">No clips loaded. Ingest a folder to get started.</p>
        </div>
      </div>
      <ClipDetail />
    </div>
  );
}
