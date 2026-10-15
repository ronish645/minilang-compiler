import { useCallback, useEffect, useRef } from "react";
import { useSearchParams } from "react-router-dom";
import { SECTION_IDS } from "../lib/sections";

// Deep links jump straight to the section; nav clicks follow the page's CSS
// scroll-behavior (smooth, or instant under prefers-reduced-motion).
const scrollToSection = (id: string, behavior: ScrollBehavior = "auto") =>
  document.getElementById(id)?.scrollIntoView({ block: "start", behavior });

/**
 * URL state for the page: ?run=<id> picks the run, ?section=<id> is the deep
 * link other pages use. The section is scrolled into view once, after the data
 * has rendered; later nav clicks scroll directly and keep the URL in sync.
 */
export function useBenchmarkParams(ready: boolean) {
  const [params, setParams] = useSearchParams();
  const runParam = params.get("run");
  const section = params.get("section");
  const scrolled = useRef(false);

  useEffect(() => {
    if (!ready || scrolled.current) return;
    scrolled.current = true;
    if (!section || !SECTION_IDS.includes(section)) return;
    const frame = requestAnimationFrame(() => scrollToSection(section, "instant"));
    return () => cancelAnimationFrame(frame);
  }, [ready, section]);

  const update = useCallback(
    (key: string, value: string) =>
      setParams(
        (current) => {
          const next = new URLSearchParams(current);
          next.set(key, value);
          return next;
        },
        { replace: true, preventScrollReset: true },
      ),
    [setParams],
  );

  const setRun = useCallback((id: string) => update("run", id), [update]);
  const goToSection = useCallback(
    (id: string) => {
      scrollToSection(id);
      update("section", id);
    },
    [update],
  );

  return { runParam, setRun, goToSection };
}
