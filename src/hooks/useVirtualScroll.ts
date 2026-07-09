import { useRef, useState, useEffect, useCallback } from "react";

export function useVirtualScroll(totalItems: number, itemHeight: number) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 });

  const onScroll = useCallback(() => {
    // TODO: calculate visible range based on scroll position and container height
    void totalItems;
    void itemHeight;
  }, [totalItems, itemHeight]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener("scroll", onScroll);
    return () => el.removeEventListener("scroll", onScroll);
  }, [onScroll]);

  return { containerRef, visibleRange, setVisibleRange };
}
