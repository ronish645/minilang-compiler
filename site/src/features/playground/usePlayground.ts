import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import type { EditorMarker } from "./editor/errorMarkers";
import type { ShareState } from "./EditorToolbar";
import { CUSTOM_ID } from "./ExamplePicker";
import { DEFAULT_EXAMPLE, findExample } from "./examples";
import type { InspectorTab } from "./inspector/Inspector";
import { decodeSource, encodeSource, MAX_SHARE_BYTES } from "./shareLink";
import { useCompiler } from "./worker/useCompiler";

/** Re-check this long after the last keystroke. */
const LIVE_DEBOUNCE_MS = 350;
const SHARE_FEEDBACK_MS = 2000;

interface Loaded {
  exampleId: string;
  source: string; // what Reset restores
}

function initialProgram(code: string | null): Loaded {
  const shared = code ? decodeSource(code) : null;
  return shared !== null
    ? { exampleId: CUSTOM_ID, source: shared }
    : { exampleId: DEFAULT_EXAMPLE.id, source: DEFAULT_EXAMPLE.source };
}

/** The page's state: the program, live compiling, the active tab and sharing. */
export function usePlayground() {
  const [params, setParams] = useSearchParams();
  const [loaded, setLoaded] = useState<Loaded>(() => initialProgram(params.get("code")));
  const [source, setSource] = useState(loaded.source);
  const [tab, setTab] = useState<InspectorTab>("output");
  const [shareState, setShareState] = useState<ShareState>("idle");
  const compiler = useCompiler();
  const { explore } = compiler;
  const lastExplored = useRef<string | null>(null);
  const codeParam = params.get("code");
  const sourceRef = useRef(source);
  useEffect(() => {
    sourceRef.current = source;
  }, [source]);

  // A share link pasted into an already-open tab only changes the hash, so
  // the page stays mounted: load the program whenever ?code= changes.
  useEffect(() => {
    const shared = codeParam ? decodeSource(codeParam) : null;
    if (shared === null || shared === sourceRef.current) return;
    setLoaded({ exampleId: CUSTOM_ID, source: shared });
    setSource(shared);
    setTab("output");
  }, [codeParam]);

  const clearCodeParam = useCallback(() => {
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete("code");
        return next;
      },
      { replace: true },
    );
  }, [setParams]);

  // Editor changes: once the program no longer matches ?code=, drop the param
  // so a reload or bookmark never brings back a stale program.
  const editSource = useCallback(
    (next: string) => {
      setSource(next);
      if (codeParam !== null && decodeSource(codeParam) !== next) clearCodeParam();
    },
    [codeParam, clearCodeParam],
  );

  // Live mode: every edit (debounced) runs the whole pipeline in the worker.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (lastExplored.current === source) return;
      lastExplored.current = source;
      explore(source);
    }, LIVE_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [source, explore]);

  useEffect(() => {
    if (shareState === "idle") return;
    const timer = window.setTimeout(() => setShareState("idle"), SHARE_FEEDBACK_MS);
    return () => window.clearTimeout(timer);
  }, [shareState]);

  const run = useCallback(() => {
    lastExplored.current = source;
    explore(source);
    setTab("output");
  }, [explore, source]);

  const pickExample = useCallback(
    (id: string) => {
      const example = findExample(id);
      if (!example) return;
      setLoaded({ exampleId: example.id, source: example.source });
      setSource(example.source);
      setTab("output");
      clearCodeParam(); // the URL no longer describes the program
    },
    [clearCodeParam],
  );

  const reset = useCallback(() => editSource(loaded.source), [editSource, loaded.source]);

  const share = useCallback(async () => {
    const code = encodeSource(source);
    if (code.length > MAX_SHARE_BYTES) {
      setShareState("too-long");
      return;
    }
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("code", code);
        return next;
      },
      { replace: true },
    );
    const url = `${window.location.origin}${window.location.pathname}#/playground?code=${code}`;
    try {
      await navigator.clipboard.writeText(url);
      setShareState("copied");
    } catch {
      setShareState("failed");
    }
  }, [setParams, source]);

  const markers = useMemo<EditorMarker[]>(
    () =>
      (compiler.result?.errors ?? []).map((e) => ({
        line: e.line,
        col: e.col,
        message: e.hint ? `${e.message}\nhelp: ${e.hint}` : e.message,
      })),
    [compiler.result],
  );

  return {
    compiler,
    source,
    setSource: editSource,
    exampleId: loaded.exampleId,
    example: findExample(loaded.exampleId) ?? null,
    isModified: source !== loaded.source,
    tab,
    setTab,
    run,
    pickExample,
    reset,
    share,
    shareState,
    markers,
  };
}
