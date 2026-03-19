import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSMessage, WSMessageType } from '../types/collaborator';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Derive WS base: http://host/api → ws://host
function getWsBase(): string {
  const base = API_BASE_URL.replace('/api', '');
  return base
  .replace(/^https/, 'wss')
  .replace(/^http/, 'ws');
}

interface UseWebSocketOptions {
  tripId: number | null;
  token: string | null;              // Clerk JWT
  onMessage: (msg: WSMessage) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
}

export type WSStatus = 'connecting' | 'connected' | 'disconnected' | 'error';

export function useWebSocket({
  tripId,
  token,
  onMessage,
  onConnected,
  onDisconnected,
}: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const pingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const isMounted = useRef(true);
  const [status, setStatus] = useState<WSStatus>('disconnected');

  const cleanup = useCallback(() => {
    if (pingRef.current) clearInterval(pingRef.current);
    if (reconnectRef.current) clearTimeout(reconnectRef.current);
    if (wsRef.current) {
      wsRef.current.onclose = null; // prevent reconnect loop on manual close
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const connect = useCallback(() => {
    if (!tripId || !token || !isMounted.current) return;

    cleanup();
    setStatus('connecting');

    const url = `${getWsBase()}/ws/trips/${tripId}?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!isMounted.current) return;
      reconnectAttempts.current = 0;
      setStatus('connected');
      onConnected?.();

      // Heartbeat ping every 25s to keep connection alive
      pingRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        }
      }, 25000);
    };

    ws.onmessage = (event) => {
      if (!isMounted.current) return;
      try {
        const msg: WSMessage = JSON.parse(event.data);
        if (msg.type !== 'pong') onMessage(msg);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onerror = () => {
      if (!isMounted.current) return;
      setStatus('error');
    };

    ws.onclose = () => {
      if (!isMounted.current) return;
      setStatus('disconnected');
      onDisconnected?.();
      if (pingRef.current) clearInterval(pingRef.current);

      // Exponential backoff: 2s, 4s, 8s, max 30s
      const delay = Math.min(2000 * 2 ** reconnectAttempts.current, 30000);
      reconnectAttempts.current += 1;
      reconnectRef.current = setTimeout(connect, delay);
    };
  }, [tripId, token, onMessage, onConnected, onDisconnected, cleanup]);

  // Connect when tripId or token changes
  useEffect(() => {
    isMounted.current = true;
    connect();
    return () => {
      isMounted.current = false;
      cleanup();
    };
  }, [tripId, token]);

  const sendMessage = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { status, sendMessage };
}
