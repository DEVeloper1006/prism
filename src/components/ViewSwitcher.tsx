type View = "browser" | "timeline" | "transcript" | "assembly";

interface ViewSwitcherProps {
  activeView: View;
  onViewChange: (view: View) => void;
}

const views: { key: View; label: string }[] = [
  { key: "browser", label: "Browser" },
  { key: "timeline", label: "Timeline" },
  { key: "transcript", label: "Transcript" },
  { key: "assembly", label: "Assembly" },
];

export default function ViewSwitcher({ activeView, onViewChange }: ViewSwitcherProps) {
  return (
    <nav className="flex gap-1 px-4 py-1 bg-panel border-b border-surface">
      {views.map((v) => (
        <button
          key={v.key}
          onClick={() => onViewChange(v.key)}
          className={`px-3 py-1 text-sm rounded transition-colors ${
            activeView === v.key
              ? "bg-accent text-white"
              : "text-gray-400 hover:text-white hover:bg-surface"
          }`}
        >
          {v.label}
        </button>
      ))}
    </nav>
  );
}
