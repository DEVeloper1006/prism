import { useState } from "react";
import TopBar from "./components/TopBar";
import ViewSwitcher from "./components/ViewSwitcher";
import ClipBrowser from "./components/ClipBrowser";
import TimelineView from "./components/TimelineView";
import TranscriptView from "./components/TranscriptView";
import AssemblyWorkspace from "./components/AssemblyWorkspace";

type View = "browser" | "timeline" | "transcript" | "assembly";

export default function App() {
  const [activeView, setActiveView] = useState<View>("browser");

  return (
    <div className="flex flex-col h-screen bg-base text-white">
      <TopBar />
      <ViewSwitcher activeView={activeView} onViewChange={setActiveView} />
      <main className="flex-1 overflow-hidden">
        {activeView === "browser" && <ClipBrowser />}
        {activeView === "timeline" && <TimelineView />}
        {activeView === "transcript" && <TranscriptView />}
        {activeView === "assembly" && <AssemblyWorkspace />}
      </main>
    </div>
  );
}
