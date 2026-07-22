import { useRef, useState, useEffect, useCallback } from "react";

export function useVirtualScroll(totalItems: number, itemHeight: number) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [visibleRange, setVisibleRange] = useState({ start: 0, end: 50 });

  const onScroll = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;

    const scrollTop = el.scrollTop;
    const viewportHeight = el.clientHeight;

    const start = Math.max(0, Math.floor(scrollTop / itemHeight) - 5);
    const visible = Math.ceil(viewportHeight / itemHeight);
    const end = Math.min(totalItems, start + visible + 10);

    setVisibleRange({ start, end });
  }, [totalItems, itemHeight]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    el.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    return () => el.removeEventListener("scroll", onScroll);
  }, [onScroll]);

  const totalHeight = totalItems * itemHeight;

  return { containerRef, visibleRange, totalHeight };
}
