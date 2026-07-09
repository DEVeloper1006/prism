export default function SearchBar() {
  return (
    <div className="flex-1 relative">
      <input
        type="text"
        placeholder="Search clips with natural language..."
        className="w-full bg-surface border border-surface rounded px-3 py-1.5 text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-accent"
      />
      <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-accent bg-accent/10 px-1.5 py-0.5 rounded">
        AI
      </span>
    </div>
  );
}
