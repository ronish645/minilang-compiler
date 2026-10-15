import { ArrowRight, Check, Send, X } from "lucide-react";
import { Fragment, type ReactNode } from "react";
import { cn } from "../../../lib/cn";
import type { Episode } from "../../../lib/types";
import { usesTools } from "../filters";

function Step({ ok, children }: { ok: boolean | null; children: ReactNode }) {
  return (
    <li
      className={cn(
        "inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-xs font-medium ring-1 ring-inset",
        ok === true && "bg-good-mark/10 text-good ring-good-mark/30",
        ok === false && "bg-critical/10 text-critical ring-critical/30",
        ok === null && "bg-surface-2 text-ink-2 ring-border",
      )}
    >
      {children}
    </li>
  );
}

const Arrow = () => (
  <li aria-hidden className="text-muted">
    <ArrowRight className="size-3.5" />
  </li>
);

/** Each run_minilang call in order, then the submission. */
export function RunTimeline({ episode }: { episode: Episode }) {
  if (!usesTools(episode)) {
    return <p className="text-sm text-ink-2">One-shot: no tools. The model wrote the program once, without running it.</p>;
  }
  const note =
    episode.runs.length === 0
      ? "Never ran its code: the program was submitted without a single run_minilang call."
      : null;
  return (
    <div className="space-y-2">
      <ol className="flex flex-wrap items-center gap-1.5" aria-label="Runs, in order">
        {episode.runs.map((run, i) => (
          <Fragment key={i}>
            <Step ok={run.ok}>
              {run.ok ? <Check className="size-3.5" aria-hidden /> : <X className="size-3.5" aria-hidden />}
              Run {i + 1}
              <span className="font-normal">{run.ok ? "ok" : `${run.stage ?? "error"} error`}</span>
            </Step>
            <Arrow />
          </Fragment>
        ))}
        <Step ok={null}>
          <Send className="size-3.5" aria-hidden />
          Submitted
        </Step>
      </ol>
      {note && <p className="text-sm text-ink-2">{note}</p>}
    </div>
  );
}
