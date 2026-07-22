import { useState } from "react";
import { exportFcpxml, exportEdl } from "../lib/api";

interface ExportDialogProps {
  visible: boolean;
  clipIds: string[];
  onClose: () => void;
}

export default function ExportDialog({ visible, clipIds, onClose }: ExportDialogProps) {
  const [exporting, setExporting] = useState(false);

  if (!visible) return null;

  const handleExport = async (format: "fcpxml" | "edl") => {
    setExporting(true);
    try {
      const fn = format === "fcpxml" ? exportFcpxml : exportEdl;
      const content = await fn(clipIds);
      const blob = new Blob([content], { type: format === "fcpxml" ? "application/xml" : "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `prism_export.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      onClose();
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div className="glass rounded-xl p-6 w-80" onClick={(e) => e.stopPropagation()}>
        <h3 className="text-sm font-semibold text-text-primary mb-4">Export {clipIds.length} clips</h3>
        <div className="space-y-2">
          <button
            onClick={() => handleExport("fcpxml")}
            disabled={exporting}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface transition-colors text-sm text-text-primary disabled:opacity-50"
          >
            FCPXML (DaVinci Resolve)
          </button>
          <button
            onClick={() => handleExport("edl")}
            disabled={exporting}
            className="w-full text-left px-3 py-2 rounded-lg hover:bg-surface transition-colors text-sm text-text-primary disabled:opacity-50"
          >
            EDL (Edit Decision List)
          </button>
        </div>
        <button
          onClick={onClose}
          className="mt-4 w-full text-xs text-text-secondary hover:text-text-primary py-1"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
