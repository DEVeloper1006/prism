import { useState, useCallback } from "react";
import { useWebSocket } from "./useWebSocket";

export interface TrackProgress {
  track: string;
  current: number;
  total: number;
}

export function useIngestionProgress() {
  const [progress, setProgress] = useState(0);
  const [processed, setProcessed] = useState(0);
  const [total, setTotal] = useState(0);
  const [ingesting, setIngesting] = useState(false);
  const [currentClip, setCurrentClip] = useState<string | null>(null);
  const [currentTrack, setCurrentTrack] = useState<string | null>(null);

  const onMessage = useCallback((event: Record<string, unknown>) => {
    const type = event.type as string;

    if (type === "ingest_start") {
      setIngesting(true);
      setTotal(event.total_files as number);
      setProcessed(0);
      setProgress(0);
    } else if (type === "clip_complete") {
      setProcessed(event.processed as number);
      setProgress(event.progress as number);
      setCurrentClip(event.clip_id as string);
    } else if (type === "track_start") {
      setCurrentTrack(event.track as string);
      setCurrentClip(event.clip_id as string);
    } else if (type === "ingest_complete") {
      setIngesting(false);
      setProgress(1);
    }
  }, []);

  const { connected } = useWebSocket(onMessage as (e: unknown) => void);

  return { progress, processed, total, ingesting, currentClip, currentTrack, connected };
}
