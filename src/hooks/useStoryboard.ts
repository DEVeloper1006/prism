import { useState, useCallback } from "react";
import type { Storyboard, StoryboardCell } from "../lib/types";
import { createStoryboard, getStoryboard, updateStoryboard } from "../lib/api";

export function useStoryboard() {
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [cells, setCells] = useState<StoryboardCell[]>([]);
  const [loading, setLoading] = useState(false);

  const create = useCallback(async (name: string, mode = "post_shoot") => {
    setLoading(true);
    try {
      const { id } = await createStoryboard(name, mode);
      const sb = await getStoryboard(id);
      setStoryboard(sb);
      setCells(JSON.parse(sb.cells));
    } finally {
      setLoading(false);
    }
  }, []);

  const load = useCallback(async (id: number) => {
    setLoading(true);
    try {
      const sb = await getStoryboard(id);
      setStoryboard(sb);
      setCells(JSON.parse(sb.cells));
    } finally {
      setLoading(false);
    }
  }, []);

  const save = useCallback(async () => {
    if (!storyboard) return;
    await updateStoryboard(storyboard.id, { cells: JSON.stringify(cells) });
  }, [storyboard, cells]);

  const reorderCell = useCallback((fromIndex: number, toIndex: number) => {
    setCells((prev) => {
      const next = [...prev];
      const [moved] = next.splice(fromIndex, 1);
      next.splice(toIndex, 0, moved);
      return next;
    });
  }, []);

  const removeCell = useCallback((index: number) => {
    setCells((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const addCell = useCallback((cell: StoryboardCell) => {
    setCells((prev) => [...prev, cell]);
  }, []);

  return { storyboard, cells, loading, create, load, save, reorderCell, removeCell, addCell, setCells };
}
