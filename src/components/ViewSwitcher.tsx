import type { View } from "../lib/types";

interface ViewSwitcherProps {
  activeView: View;
  onViewChange: (view: View) => void;
}

const views: { key: View; label: string }[] = [
  { key: "browser", label: "Browser" },
  { key: "timeline", label: "Timeline" },
  { key: "transcript", label: "Transcript" },
  { key: "assembly", label: "Assembly" },
  { key: "storyboard", label: "Storyboard" },
];

export default function ViewSwitcher({ activeView, onViewChange }: ViewSwitcherProps) {
  return (
    <nav className="flex gap-1 px-4 py-1 bg-panel border-b border-border shrink-0">
      {views.map((v) => (
        <button
          key={v.key}
          onClick={() => onViewChange(v.key)}
          className={`px-3 py-1 text-xs rounded transition-colors ${
            activeView === v.key
              ? "bg-interactive text-white"
              : "text-text-secondary hover:text-text-primary hover:bg-surface"
          }`}
        >
          {v.label}
        </button>
      ))}
    </nav>
  );
}
