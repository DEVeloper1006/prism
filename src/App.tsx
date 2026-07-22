import { useState, useEffect, useCallback } from "react";
import TopBar from "./components/TopBar";
import ViewSwitcher from "./components/ViewSwitcher";
import ClipBrowser from "./components/ClipBrowser";
import TimelineView from "./components/TimelineView";
import TranscriptView from "./components/TranscriptView";
import AssemblyWorkspace from "./components/AssemblyWorkspace";
import StoryboardView from "./components/StoryboardView";
import ProgressOverlay from "./components/ProgressOverlay";
import { useClipLibrary } from "./hooks/useClipLibrary";
import { useIngestionProgress } from "./hooks/useIngestionProgress";
import { healthCheck, openProject, startIngest } from "./lib/api";
import type { View, Clip } from "./lib/types";

type AppState = "empty" | "loading" | "active";

export default function App() {
  const [appState, setAppState] = useState<AppState>("empty");
  const [activeView, setActiveView] = useState<View>("browser");
  const [selectedClip, setSelectedClip] = useState<Clip | null>(null);
  const [projectPath, setProjectPath] = useState<string | null>(null);
  const [clipCount, setClipCount] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [recentProjects, setRecentProjects] = useState<Array<{ path: string; name: string; clipCount: number; lastOpened: string }>>([]);

  const clipLibrary = useClipLibrary();
  const ingestion = useIngestionProgress();

  useEffect(() => {
    const stored = localStorage.getItem("prism_recent_projects");
    if (stored) {
      try { setRecentProjects(JSON.parse(stored)); } catch { /* ignore */ }
    }
  }, []);

  const handleOpenProject = useCallback(async (folderPath: string) => {
    setAppState("loading");
    try {
      await openProject(folderPath);
      setProjectPath(folderPath);

      const health = await healthCheck();
      setClipCount(health.clip_count);

      if (health.clip_count > 0) {
        setAppState("active");
        clipLibrary.fetchClips(0);
      } else {
        setAppState("active");
      }

      const name = folderPath.split("/").pop() || folderPath;
      const entry = { path: folderPath, name, clipCount: health.clip_count, lastOpened: new Date().toISOString() };
      const updated = [entry, ...recentProjects.filter(p => p.path !== folderPath)].slice(0, 10);
      setRecentProjects(updated);
      localStorage.setItem("prism_recent_projects", JSON.stringify(updated));
    } catch {
      setAppState("empty");
    }
  }, [clipLibrary, recentProjects]);

  const handleStartIngest = useCallback(async () => {
    if (!projectPath) return;
    await startIngest(projectPath);
  }, [projectPath]);

  const handleDrop = useCallback(async (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const items = e.dataTransfer.items;
    if (items.length > 0) {
      const entry = items[0].webkitGetAsEntry?.();
      if (entry?.isDirectory) {
        const path = (e.dataTransfer.files[0] as unknown as { path?: string })?.path;
        if (path) handleOpenProject(path);
      }
    }
  }, [handleOpenProject]);

  const handleBrowse = useCallback(async () => {
    try {
      const { openFolder } = await import("./lib/tauri");
      const folder = await openFolder();
      if (folder) handleOpenProject(folder);
    } catch {
      // fallback for browser dev
    }
  }, [handleOpenProject]);

  useEffect(() => {
    if (!ingestion.ingesting && ingestion.progress >= 1 && appState === "active") {
      clipLibrary.refresh();
      healthCheck().then(h => setClipCount(h.clip_count)).catch(() => {});
    }
  }, [ingestion.ingesting, ingestion.progress]);

  if (appState === "empty" || appState === "loading") {
    return (
      <div className="flex flex-col h-screen bg-base">
        <TopBar clipCount={0} projectName={null} />
        <div
          className="flex-1 flex flex-col items-center justify-center px-8"
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
        >
          <div className="mb-8 text-center">
            <div className="text-4xl font-semibold tracking-tight text-text-primary mb-2">PRISM</div>
            <div className="text-text-secondary text-sm">Footage intelligence for filmmakers</div>
          </div>

          <div
            className={`w-full max-w-lg rounded-xl border border-dashed p-16 text-center transition-colors ${
              dragOver
                ? "border-interactive bg-interactive/5"
                : "border-border"
            }`}
          >
            <div className="text-text-tertiary text-4xl mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-12 h-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
              </svg>
            </div>
            <div className="text-text-secondary mb-2">
              {dragOver ? "Release to open" : "Drop a folder to start"}
            </div>
            <div className="text-text-tertiary text-sm mb-4">or</div>
            <button
              onClick={handleBrowse}
              className="text-interactive text-sm hover:underline"
            >
              Browse...
            </button>
          </div>

          {recentProjects.length > 0 && (
            <div className="mt-8 w-full max-w-lg">
              <div className="text-text-secondary text-xs font-semibold mb-2">Recent Projects</div>
              {recentProjects.map((project) => (
                <button
                  key={project.path}
                  onClick={() => handleOpenProject(project.path)}
                  className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface transition-colors flex justify-between items-center"
                >
                  <div>
                    <div className="text-text-primary text-sm">{project.name}</div>
                    <div className="text-text-tertiary text-xs">{project.path}</div>
                  </div>
                  <div className="text-text-tertiary text-xs tabular-nums">
                    {project.clipCount} clips
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-base text-text-primary">
      <TopBar clipCount={clipCount} projectName={projectPath?.split("/").pop() ?? null} />
      <ViewSwitcher activeView={activeView} onViewChange={setActiveView} />
      <main className="flex-1 overflow-hidden">
        {activeView === "browser" && (
          <ClipBrowser
            clips={clipLibrary.clips}
            loading={clipLibrary.loading}
            selectedClip={selectedClip}
            onSelectClip={setSelectedClip}
            onSearch={clipLibrary.searchClips}
            onLoadMore={clipLibrary.loadMore}
            onStartIngest={handleStartIngest}
          />
        )}
        {activeView === "timeline" && <TimelineView clips={clipLibrary.clips} />}
        {activeView === "transcript" && <TranscriptView selectedClip={selectedClip} />}
        {activeView === "assembly" && <AssemblyWorkspace clips={clipLibrary.clips} />}
        {activeView === "storyboard" && <StoryboardView clips={clipLibrary.clips} />}
      </main>
      <ProgressOverlay
        visible={ingestion.ingesting}
        progress={ingestion.progress}
        processed={ingestion.processed}
        total={ingestion.total}
        currentClip={ingestion.currentClip}
        currentTrack={ingestion.currentTrack}
      />
    </div>
  );
}
