import { useState } from "react";

export interface TrackProgress {
  track: string;
  current: number;
  total: number;
}

export function useIngestionProgress() {
  const [progress, setProgress] = useState<TrackProgress[]>([]);
  const [ingesting, setIngesting] = useState(false);

  // TODO: subscribe to WebSocket progress events

  return { progress, ingesting, setProgress, setIngesting };
}
