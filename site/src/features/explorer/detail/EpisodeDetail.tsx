import { ChevronLeft, ChevronRight, Info, X } from "lucide-react";
import { useEffect, useRef } from "react";
import { Button } from "../../../components/ui/Button";
import { ModelChip } from "../../../components/ui/ModelChip";
import { count, seconds, usd } from "../../../lib/format";
import type { Episode } from "../../../lib/types";
import { MiniLangCode } from "../../overview/code/MiniLangCode";
import type { Lookups } from "../lookups";
import { OutcomeBadge } from "../OutcomeBadge";
import { CopyLinkButton } from "./CopyLinkButton";
import { DetailSection } from "./DetailSection";
import { OutputDiff } from "./OutputDiff";
import { RunTimeline } from "./RunTimeline";

export const DETAIL_TITLE_ID = "episode-detail-title";

interface EpisodeDetailProps {
  episode: Episode;
  lookups: Lookups;
  position: { index: number; total: number } | null; // null: not in the filtered list
  onPrev: () => void;
  onNext: () => void;
  onClose: () => void;
}

function Header({ episode, lookups, onClose }: Pick<EpisodeDetailProps, "episode" | "lookups" | "onClose">) {
  return (
    <header className="border-b border-border px-5 py-4 sm:px-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted">
            Tier {episode.tier} · run <span className="font-mono">{episode.run}</span>
          </p>
          <h2 id={DETAIL_TITLE_ID} className="mt-1 break-all font-mono text-lg font-semibold text-ink">
            {episode.task}
          </h2>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close episode"
          className="grid size-9 shrink-0 place-items-center rounded-lg text-ink-2 transition hover:bg-surface-2 hover:text-ink"
        >
          <X className="size-4" aria-hidden />
        </button>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <ModelChip model={episode.model} />
        <span className="text-ink-2">{lookups.conditionLabel(episode.condition)}</span>
        <OutcomeBadge outcome={episode.outcome} />
      </div>
    </header>
  );
}

function Stats({ episode }: { episode: Episode }) {
  const items = [
    { label: "Turns", value: count(episode.turns) },
    { label: "Runs", value: count(episode.runs.length) },
    { label: "Time", value: seconds(episode.seconds) },
    { label: "Cost", value: usd(episode.cost_usd) },
  ];
  return (
    <dl className="grid grid-cols-4 divide-x divide-border rounded-xl border border-border bg-surface-2/50">
      {items.map((item) => (
        <div key={item.label} className="px-3 py-2.5">
          <dt className="text-xs text-muted">{item.label}</dt>
          <dd className="mt-0.5 font-semibold tabular-nums text-ink">{item.value}</dd>
        </div>
      ))}
    </dl>
  );
}

// Prev/Next stay focusable at the list ends (aria-disabled, not disabled), so
// keyboard focus never drops to <body> after stepping to the first or last item.
const STEP_CLASS = "aria-disabled:cursor-not-allowed aria-disabled:opacity-50 aria-disabled:hover:bg-transparent";

function Footer({ position, onPrev, onNext }: Pick<EpisodeDetailProps, "position" | "onPrev" | "onNext">) {
  const atStart = !position || position.index === 0;
  const atEnd = !position || position.index >= position.total - 1;
  return (
    <footer className="flex items-center justify-between gap-2 border-t border-border px-5 py-3 sm:px-6">
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          variant="ghost"
          className={STEP_CLASS}
          aria-disabled={atStart}
          onClick={() => !atStart && onPrev()}
          aria-label="Previous episode"
          icon={<ChevronLeft className="size-4" aria-hidden />}
        >
          <span className="hidden sm:inline">Prev</span>
        </Button>
        <span className="text-xs tabular-nums text-muted" aria-live="polite">
          {position ? `${position.index + 1} of ${position.total}` : "Not in current filter"}
        </span>
        <Button
          size="sm"
          variant="ghost"
          className={STEP_CLASS}
          aria-disabled={atEnd}
          onClick={() => !atEnd && onNext()}
          aria-label="Next episode"
        >
          <span className="hidden sm:inline">Next</span>
          <ChevronRight className="size-4" aria-hidden />
        </Button>
      </div>
      <CopyLinkButton />
    </footer>
  );
}

export function EpisodeDetail({ episode, lookups, position, onPrev, onNext, onClose }: EpisodeDetailProps) {
  const task = lookups.task(episode.task);
  const bodyRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bodyRef.current?.scrollTo({ top: 0 }); // each episode starts at its header
  }, [episode.id]);
  return (
    <>
      <Header episode={episode} lookups={lookups} onClose={onClose} />
      <div ref={bodyRef} className="flex-1 space-y-7 overflow-y-auto px-5 py-5 sm:px-6">
        <Stats episode={episode} />

        {task && (
          <DetailSection title="Task">
            <p className="text-sm text-ink">{task.prompt}</p>
          </DetailSection>
        )}

        <DetailSection title="Submitted program">
          {episode.code ? (
            <div className="overflow-hidden rounded-xl border border-border">
              <MiniLangCode code={episode.code} lineNumbers label="Submitted MiniLang program" className="max-h-[28rem] overflow-y-auto bg-code px-3 py-3" />
            </div>
          ) : (
            <p className="rounded-xl border border-dashed border-border-strong px-3 py-3 text-sm text-ink-2">The model submitted no code.</p>
          )}
        </DetailSection>

        <DetailSection title="Runs">
          <RunTimeline episode={episode} />
        </DetailSection>

        {episode.error && (
          <DetailSection title="Final error">
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-xl border border-critical/30 bg-critical/5 px-3 py-2.5 font-mono text-[13px] text-ink">{episode.error}</pre>
          </DetailSection>
        )}

        {task && (
          <DetailSection title="Output vs expected">
            <OutputDiff output={episode.output} expected={task.expected} />
          </DetailSection>
        )}

        <p className="flex gap-2 rounded-xl bg-surface-2 px-3 py-2.5 text-xs text-ink-2">
          <Info className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          Recorded per episode: the final program, the result of each run and the graded output. The full conversation with the model is not stored.
        </p>
      </div>
      <Footer position={position} onPrev={onPrev} onNext={onNext} />
    </>
  );
}
