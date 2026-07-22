import { useWatchFolder } from "../hooks/useWatchFolder";

export default function WatchFolderIndicator() {
  const { config } = useWatchFolder();

  if (!config.active) return null;

  return (
    <div className="flex items-center gap-1.5">
      <div className="w-1.5 h-1.5 rounded-full bg-track-technical animate-pulse" />
      <span className="text-xs text-text-tertiary">Watching</span>
    </div>
  );
}
