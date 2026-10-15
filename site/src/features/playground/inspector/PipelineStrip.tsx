import { Check, ChevronRight, Minus, X } from "lucide-react";
import { Fragment } from "react";
import { cn } from "../../../lib/cn";
import { formatMs, PIPELINE, stageStatus, type StageStatus } from "../pipeline";
import type { ExploreResult } from "../worker/protocol";

const ICONS: Record<StageStatus, typeof Check> = {
  passed: Check,
  failed: X,
  skipped: Minus,
  idle: Minus,
};

const STATUS_TEXT: Record<StageStatus, string> = {
  passed: "passed",
  failed: "failed",
  skipped: "skipped",
  idle: "not run yet",
};

interface PipelineStripProps {
  result: ExploreResult | null;
  running: boolean;
}

/** Lexer → Parser → Type checker → Codegen → Interpreter, with each stage's state and time. */
export function PipelineStrip({ result, running }: PipelineStripProps) {
  return (
    <ol
      aria-label="Compiler pipeline"
      className={cn(
        "relative flex items-stretch gap-0.5 overflow-x-auto pb-1 transition-opacity",
        running && "opacity-70",
      )}
    >
      {PIPELINE.map((stage, i) => {
        const status = stageStatus(result, stage);
        const Icon = ICONS[status];
        return (
          <Fragment key={stage.key}>
            {i > 0 && (
              <li aria-hidden className="flex items-center text-muted">
                <ChevronRight className="size-3" />
              </li>
            )}
            <li
              className={cn(
                "relative flex min-w-fit flex-1 flex-col gap-0.5 rounded-lg border px-2 py-1.5",
                status === "failed"
                  ? "border-critical/40 bg-critical/10"
                  : status === "passed"
                    ? "border-border bg-surface"
                    : "border-dashed border-border bg-transparent",
              )}
            >
              <span className="flex items-center gap-1.5 text-xs font-medium text-ink">
                <Icon
                  aria-hidden
                  className={cn(
                    "size-3.5 shrink-0",
                    status === "passed" && "text-good-mark",
                    status === "failed" && "text-critical",
                    (status === "skipped" || status === "idle") && "text-muted",
                  )}
                />
                <span className="whitespace-nowrap">{stage.label}</span>
                <span className="sr-only">: {STATUS_TEXT[status]}</span>
              </span>
              <span className="pl-5 font-mono [font-variant-ligatures:none] text-[11px] tabular-nums text-muted">
                {status === "skipped" ? "skipped" : formatMs(result?.timings_ms[stage.key])}
              </span>
            </li>
          </Fragment>
        );
      })}
    </ol>
  );
}
