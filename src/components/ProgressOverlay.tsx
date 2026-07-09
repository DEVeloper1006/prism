interface ProgressOverlayProps {
  visible: boolean;
}

export default function ProgressOverlay({ visible }: ProgressOverlayProps) {
  if (!visible) return null;

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50">
      <div className="bg-panel rounded-lg p-6 w-96">
        <h3 className="text-sm font-semibold text-white mb-4">Ingesting...</h3>
        <p className="text-xs text-gray-400">Progress bars will appear here per track.</p>
      </div>
    </div>
  );
}
