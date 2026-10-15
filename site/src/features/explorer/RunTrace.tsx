import { Check, X } from "lucide-react";
import { cn } from "../../lib/cn";
import type { Episode } from "../../lib/types";
import { usesTools } from "./filters";

export function describeRuns(episode: Episode): string {
  if (!usesTools(episode)) return "One-shot: no tools";
  if (episode.runs.length === 0) return "Never ran its code";
  return episode.runs
    .map((run, i) => `Run ${i + 1} ${run.ok ? "passed" : `failed${run.stage ? ` (${run.stage})` : ""}`}`)
    .join(", ");
}

/** One small mark per run_minilang call: a check for a clean run, a cross for an error. */
export function RunTrace({ episode }: { episode: Episode }) {
  const label = describeRuns(episode);
  if (episode.runs.length === 0) {
    return (
      <span className="text-xs text-muted" title={label}>
        {usesTools(episode) ? "not run" : "no tools"}
      </span>
    );
  }
  return (
    <span role="img" aria-label={label} title={label} className="inline-flex items-center gap-1">
      {episode.runs.map((run, i) => (
        <span
          key={i}
          className={cn(
            "grid size-4 place-items-center rounded-full",
            run.ok ? "bg-good-mark/15 text-good" : "bg-critical/12 text-critical",
          )}
        >
          {run.ok ? <Check className="size-2.5" strokeWidth={3} /> : <X className="size-2.5" strokeWidth={3} />}
        </span>
      ))}
    </span>
  );
}
