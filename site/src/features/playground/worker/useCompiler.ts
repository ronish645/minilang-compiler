import { useCallback, useEffect, useRef, useState } from "react";
import type { ExploreResult, WorkerRequest, WorkerResponse } from "./protocol";

/** A request that takes longer than this is treated as hung: the worker is replaced. */
const WATCHDOG_MS = 8000;

export type CompilerStatus = "loading" | "ready" | "running" | "error";

export interface CompilerState {
  status: CompilerStatus;
  /** What the loader is doing right now ("Downloading Python runtime…"). */
  progress: string;
  /** Why the compiler can't be used (failed boot, crashed request). */
  error: string | null;
  /** A one-off notice, e.g. that a program was stopped by the watchdog. */
  notice: string | null;
  result: ExploreResult | null;
  pythonVersion: string | null;
}

const INITIAL: CompilerState = {
  status: "loading",
  progress: "Starting…",
  error: null,
  notice: null,
  result: null,
  pythonVersion: null,
};

const createWorker = () =>
  new Worker(new URL("./compiler.worker.ts", import.meta.url), { type: "module" });

/**
 * Owns the compiler worker. `explore(source)` is "latest wins": while one
 * request runs, newer sources replace each other in a single pending slot, so
 * fast typing never builds a queue.
 */
export function useCompiler() {
  const [state, setState] = useState<CompilerState>(INITIAL);
  const workerRef = useRef<Worker | null>(null);
  const readyRef = useRef(false);
  const inFlightRef = useRef<number | null>(null);
  const pendingRef = useRef<string | null>(null);
  const nextIdRef = useRef(1);
  const watchdogRef = useRef<number | undefined>(undefined);

  const send = useCallback((source: string) => {
    const worker = workerRef.current;
    if (!worker) return;
    const id = nextIdRef.current++;
    inFlightRef.current = id;
    worker.postMessage({ type: "explore", id, source } satisfies WorkerRequest);
    setState((s) => ({ ...s, status: "running" }));
    window.clearTimeout(watchdogRef.current);
    watchdogRef.current = window.setTimeout(() => restartRef.current(), WATCHDOG_MS);
  }, []);

  const flushPending = useCallback(() => {
    const next = pendingRef.current;
    pendingRef.current = null;
    if (next !== null) send(next);
    else setState((s) => (s.status === "running" ? { ...s, status: "ready" } : s));
  }, [send]);

  const handleMessage = useCallback(
    (event: MessageEvent<WorkerResponse>) => {
      const message = event.data;
      switch (message.type) {
        case "progress":
          setState((s) => ({ ...s, status: "loading", progress: message.message }));
          return;
        case "ready":
          readyRef.current = true;
          setState((s) => ({ ...s, status: "ready", pythonVersion: message.pythonVersion }));
          flushPending();
          return;
        case "result":
        case "error": {
          if (message.type === "error" && message.id === null) {
            setState((s) => ({ ...s, status: "error", error: message.message }));
            return;
          }
          if (message.id !== inFlightRef.current) return; // a stale reply
          window.clearTimeout(watchdogRef.current);
          inFlightRef.current = null;
          setState((s) =>
            message.type === "result"
              ? { ...s, result: message.result, error: null }
              : { ...s, error: message.message },
          );
          flushPending();
        }
      }
    },
    [flushPending],
  );

  const start = useCallback(() => {
    const worker = createWorker();
    worker.onmessage = handleMessage;
    worker.onerror = (event) => {
      setState((s) => ({ ...s, status: "error", error: event.message || "The compiler worker crashed." }));
    };
    workerRef.current = worker;
    readyRef.current = false;
    inFlightRef.current = null;
  }, [handleMessage]);

  // Kill a hung worker and boot a fresh one (the browser cache makes the reload quick).
  // The pending slot is kept: an edit typed while the worker hung still gets
  // compiled once the new worker reports ready. The hung source is not retried.
  const restart = useCallback(() => {
    window.clearTimeout(watchdogRef.current);
    workerRef.current?.terminate();
    setState((s) => ({
      ...s,
      status: "loading",
      progress: "Restarting the compiler…",
      notice: `The program ran for more than ${WATCHDOG_MS / 1000} seconds, so it was stopped and the compiler was restarted.`,
    }));
    start();
  }, [start]);

  /** Boot a fresh worker after a failed start (e.g. the CDN was unreachable). */
  const retry = useCallback(() => {
    window.clearTimeout(watchdogRef.current);
    workerRef.current?.terminate();
    setState((s) => ({ ...s, status: "loading", progress: "Starting…", error: null, notice: null }));
    start();
  }, [start]);
  const restartRef = useRef(restart);
  useEffect(() => {
    restartRef.current = restart;
  }, [restart]);

  useEffect(() => {
    start();
    return () => {
      window.clearTimeout(watchdogRef.current);
      workerRef.current?.terminate();
      workerRef.current = null;
    };
  }, [start]);

  const explore = useCallback(
    (source: string) => {
      setState((s) => (s.notice ? { ...s, notice: null } : s));
      if (!readyRef.current || inFlightRef.current !== null) {
        pendingRef.current = source;
        return;
      }
      send(source);
    },
    [send],
  );

  return { ...state, explore, retry };
}
