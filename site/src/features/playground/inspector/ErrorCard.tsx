import { Lightbulb } from "lucide-react";
import { Badge } from "../../../components/ui/Badge";
import { STAGE_LABEL } from "../pipeline";
import type { CompileError } from "../worker/protocol";

/** One compiler error: stage, message, position and the fix-it hint. */
export function ErrorCard({ error }: { error: CompileError }) {
  return (
    <li className="rounded-xl border border-border bg-surface p-3.5">
      <div className="flex flex-wrap items-center gap-2">
        <Badge tone="critical">{STAGE_LABEL[error.stage]}</Badge>
        <span className="font-mono text-xs text-muted">
          line {error.line}:{error.col}
        </span>
      </div>
      <p className="mt-2 text-sm font-medium text-ink">{error.message}</p>
      {error.hint && (
        <p className="mt-2 flex items-start gap-2 rounded-lg bg-warning/10 px-2.5 py-2 text-sm text-ink-2">
          <Lightbulb className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
          <span>
            <span className="sr-only">Hint: </span>
            {error.hint}
          </span>
        </p>
      )}
    </li>
  );
}
