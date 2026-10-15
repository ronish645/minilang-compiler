import { CircleCheck, CircleX, Terminal } from "lucide-react";
import { STAGE_LABEL } from "../pipeline";
import type { ExploreResult } from "../worker/protocol";
import { ErrorCard } from "./ErrorCard";

function TerminalView({ result }: { result: ExploreResult }) {
  const ran = result.ok || result.failed_stage === "runtime";
  return (
    <div className="overflow-hidden rounded-xl border border-border bg-code">
      <div className="flex items-center gap-2 border-b border-border px-3 py-2 text-xs text-muted">
        <Terminal className="size-3.5" aria-hidden />
        <span>stdout</span>
        <span className="ml-auto tabular-nums">
          {result.output.length} {result.output.length === 1 ? "line" : "lines"}
        </span>
      </div>
      <pre
        aria-label="Program output"
        className="max-h-[360px] overflow-auto px-3 py-2.5 font-mono text-[13px] leading-relaxed text-ink"
      >
        {result.output.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap break-words">
            {line === "" ? " " : line}
          </div>
        ))}
        {!ran && (
          <div className="text-muted">
            Not run: {STAGE_LABEL[result.failed_stage ?? "syntax"].toLowerCase()} errors stop the
            program before it starts.
          </div>
        )}
        {ran && result.output.length === 0 && <div className="text-muted">(no output)</div>}
        {result.ok && (
          <div className="mt-1 flex items-center gap-1.5 text-good">
            <CircleCheck className="size-3.5" aria-hidden /> exited normally
          </div>
        )}
        {result.failed_stage === "runtime" && (
          <div className="mt-1 flex items-center gap-1.5 text-critical">
            <CircleX className="size-3.5" aria-hidden /> stopped by a runtime error
          </div>
        )}
      </pre>
    </div>
  );
}

/** Program output, then (on failure) the compiler's diagnostic and one card per error. */
export function OutputPanel({ result }: { result: ExploreResult }) {
  const count = result.errors.length;
  return (
    <div className="space-y-4" aria-live="polite">
      <TerminalView result={result} />
      {count > 0 && (
        <section aria-label="Errors" className="space-y-3">
          <h3 className="text-sm font-semibold text-ink">
            {count} {count === 1 ? "error" : "errors"}
          </h3>
          <ul className="space-y-2.5">
            {result.errors.map((error, i) => (
              <ErrorCard key={`${error.line}:${error.col}:${i}`} error={error} />
            ))}
          </ul>
          {result.diagnostic && (
            <details open className="group rounded-xl border border-border bg-code">
              <summary className="cursor-pointer select-none px-3 py-2 text-xs font-medium text-ink-2 hover:text-ink">
                Diagnostic, exactly as the CLI prints it
              </summary>
              <pre className="overflow-x-auto border-t border-border px-3 py-2.5 font-mono text-[12.5px] leading-relaxed text-ink-2">
                {result.diagnostic}
              </pre>
            </details>
          )}
        </section>
      )}
    </div>
  );
}
