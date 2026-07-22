import { useState, useCallback, useEffect } from "react";
import type { WatchConfig } from "../lib/types";
import { getWatchStatus, configureWatch } from "../lib/api";

export function useWatchFolder() {
  const [config, setConfig] = useState<WatchConfig>({ folder_path: null, active: false, last_scan: null });

  const refresh = useCallback(async () => {
    try {
      const status = await getWatchStatus();
      setConfig(status);
    } catch { /* backend not ready */ }
  }, []);

  const toggle = useCallback(async (folderPath: string | null, active: boolean) => {
    await configureWatch(folderPath, active);
    await refresh();
  }, [refresh]);

  useEffect(() => { refresh(); }, [refresh]);

  return { config, toggle, refresh };
}
