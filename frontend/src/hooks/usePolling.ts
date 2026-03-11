import { useEffect, useRef, useCallback } from 'react';

interface UsePollingOptions {
  fn: () => Promise<void>;       // async function to call on each tick
  interval: number;              // ms between polls
  enabled: boolean;              // pause when false (e.g. WS is connected)
}

export function usePolling({ fn, interval, enabled }: UsePollingOptions) {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const fnRef = useRef(fn);
  fnRef.current = fn; // always latest fn without re-registering interval

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      stop();
      return;
    }
    timerRef.current = setInterval(() => fnRef.current(), interval);
    return stop;
  }, [enabled, interval, stop]);
}
