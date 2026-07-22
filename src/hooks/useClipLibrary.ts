import { useState, useCallback, useEffect } from "react";
import type { Clip, SearchQuery } from "../lib/types";
import { getClips, search } from "../lib/api";
import { PAGE_SIZE } from "../lib/constants";

export function useClipLibrary() {
  const [clips, setClips] = useState<Clip[]>([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);

  const fetchClips = useCallback(async (pageNum = 0) => {
    setLoading(true);
    try {
      const result = await getClips(pageNum * PAGE_SIZE, PAGE_SIZE);
      if (pageNum === 0) {
        setClips(result);
      } else {
        setClips((prev) => [...prev, ...result]);
      }
      setHasMore(result.length === PAGE_SIZE);
      setPage(pageNum);
    } catch {
      // backend not ready
    } finally {
      setLoading(false);
    }
  }, []);

  const searchClips = useCallback(async (query: SearchQuery) => {
    setLoading(true);
    try {
      const result = await search(query);
      setClips(result);
      setHasMore(false);
    } catch {
      setClips([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      fetchClips(page + 1);
    }
  }, [loading, hasMore, page, fetchClips]);

  const refresh = useCallback(() => fetchClips(0), [fetchClips]);

  return { clips, loading, hasMore, fetchClips, searchClips, loadMore, refresh };
}
