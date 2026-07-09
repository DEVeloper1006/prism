import { useState } from "react";
import type { Clip } from "../lib/types";

export function useClipLibrary() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(false);

  // TODO: fetch clips from backend with pagination, search, and filter support

  return { clips, loading, setClips, setLoading };
}
