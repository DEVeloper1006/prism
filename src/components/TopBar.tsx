interface TopBarProps {
  clipCount: number;
  projectName: string | null;
}

export default function TopBar({ clipCount, projectName }: TopBarProps) {
  return (
    <header className="flex items-center justify-between px-4 h-11 bg-panel border-b border-border shrink-0" style={{ WebkitAppRegion: "drag" } as React.CSSProperties}>
      <div className="flex items-center gap-3" style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}>
        <span className="text-text-primary font-semibold text-sm tracking-tight">PRISM</span>
        {projectName && (
          <span className="text-text-secondary text-xs">{projectName}</span>
        )}
      </div>
      <div className="flex items-center gap-4 text-xs text-text-secondary tabular-nums" style={{ WebkitAppRegion: "no-drag" } as React.CSSProperties}>
        <span>{clipCount} clips</span>
      </div>
    </header>
  );
}
