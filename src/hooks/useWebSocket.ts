import { useEffect, useRef, useState, useCallback } from "react";
import { WS_URL } from "../lib/constants";

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    // TODO: establish WS connection to backend with auto-reconnect
    void WS_URL;
    setConnected(false);
  }, []);

  useEffect(() => {
    connect();
    return () => wsRef.current?.close();
  }, [connect]);

  return { connected };
}
