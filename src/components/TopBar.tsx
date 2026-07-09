export default function TopBar() {
  return (
    <header className="flex items-center justify-between px-4 py-2 bg-panel border-b border-surface">
      <div className="flex items-center gap-3">
        <span className="text-accent font-bold text-lg tracking-tight">PRISM</span>
        <span className="text-sm text-gray-400">No project loaded</span>
      </div>
      <div className="flex items-center gap-4 text-sm text-gray-400">
        <span className="font-mono">0 clips</span>
      </div>
    </header>
  );
}
