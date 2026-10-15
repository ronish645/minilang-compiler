import { RotateCcw, TimerOff } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { ErrorState } from "../../components/ui/StateViews";
import { formatMs, totalMs } from "./pipeline";
import { Inspector, type InspectorTab } from "./inspector/Inspector";
import { InspectorSkeleton } from "./inspector/InspectorSkeleton";
import { PipelineStrip } from "./inspector/PipelineStrip";
import type { Token } from "./worker/protocol";
import type { CompilerState } from "./worker/useCompiler";

interface InspectorPaneProps {
  compiler: CompilerState;
  onRetry: () => void;
  tab: InspectorTab;
  onTabChange: (tab: InspectorTab) => void;
  onHoverToken: (token: Token | null) => void;
}

function StatusLine({ compiler }: { compiler: CompilerState }) {
  const { status, result } = compiler;
  const text =
    status === "loading"
      ? compiler.progress
      : status === "running"
        ? "Compiling…"
        : result
          ? `${result.ok ? "Compiled and ran" : "Stopped at an error"} in ${formatMs(totalMs(result))}`
          : "Ready";
  return (
    <p className="flex items-center gap-2 text-xs text-ink-2" aria-live="polite">
      <span
        aria-hidden
        className={
          status === "error"
            ? "size-2 rounded-full bg-critical"
            : status === "ready"
              ? "size-2 rounded-full bg-good-mark"
              : "size-2 animate-pulse rounded-full bg-warning"
        }
      />
      {text}
      {compiler.pythonVersion && (
        <span className="ml-auto text-muted">Pyodide {compiler.pythonVersion}</span>
      )}
    </p>
  );
}

/** The pipeline strip plus tabs over every stage's output. */
export function InspectorPane({ compiler, onRetry, tab, onTabChange, onHoverToken }: InspectorPaneProps) {
  const { result } = compiler;
  return (
    <section
      aria-label="Compiler inspector"
      className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
    >
      <div className="space-y-3 border-b border-border bg-surface-2/40 px-4 py-3">
        <StatusLine compiler={compiler} />
        <PipelineStrip result={result} running={compiler.status === "running"} />
      </div>
      <div className="min-h-[320px] flex-1 overflow-y-auto px-4 pb-5 pt-2">
        {compiler.notice && (
          <div role="alert" className="mt-2 flex items-start gap-2 rounded-xl border border-warning/40 bg-warning/10 p-3 text-sm text-ink">
            <TimerOff className="mt-0.5 size-4 shrink-0 text-warning" aria-hidden />
            {compiler.notice}
          </div>
        )}
        {compiler.error && (
          <div className="mt-2 space-y-2">
            <ErrorState message={compiler.error} />
            {compiler.status === "error" && (
              <Button size="sm" onClick={onRetry} icon={<RotateCcw className="size-3.5" aria-hidden />}>
                Retry
              </Button>
            )}
          </div>
        )}
        {result ? (
          <Inspector result={result} tab={tab} onTabChange={onTabChange} onHoverToken={onHoverToken} />
        ) : (
          compiler.status !== "error" && (
            <div className="pt-4">
              <InspectorSkeleton progress={compiler.progress} />
            </div>
          )
        )}
      </div>
    </section>
  );
}
