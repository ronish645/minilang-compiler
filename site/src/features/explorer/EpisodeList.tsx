import { ChevronRight } from "lucide-react";
import { ModelChip } from "../../components/ui/ModelChip";
import { cn } from "../../lib/cn";
import { modelShort } from "../../lib/models";
import { seconds, usd } from "../../lib/format";
import type { Episode } from "../../lib/types";
import type { Lookups } from "./lookups";
import { OutcomeBadge } from "./OutcomeBadge";
import { RunTrace } from "./RunTrace";

interface EpisodeListProps {
  episodes: Episode[];
  lookups: Lookups;
  selectedId: string | null;
  onOpen: (id: string) => void;
}

const openLabel = (episode: Episode, lookups: Lookups) =>
  `Open episode: ${episode.task}, ${modelShort(episode.model)}, ${lookups.conditionLabel(episode.condition)}`;

function TaskCell({ episode }: { episode: Episode }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span className="font-mono text-[13px] text-ink">{episode.task}</span>
      <span className="rounded bg-surface-2 px-1.5 text-[11px] font-medium text-ink-2">T{episode.tier}</span>
    </span>
  );
}

/** Desktop: a dense table. A real button in the task cell makes each row keyboard-reachable. */
function EpisodeTable({ episodes, lookups, selectedId, onOpen }: EpisodeListProps) {
  const th = "px-3 py-2.5 text-left text-xs font-medium uppercase tracking-wide text-muted";
  return (
    <div className="hidden overflow-x-auto rounded-2xl border border-border bg-surface md:block">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-surface-2/60">
          <tr>
            <th scope="col" className={cn(th, "pl-4")}>Task</th>
            <th scope="col" className={th}>Model</th>
            <th scope="col" className={th}>Condition</th>
            <th scope="col" className={th}>Outcome</th>
            <th scope="col" className={th}>Runs</th>
            <th scope="col" className={cn(th, "text-right")}>Time</th>
            <th scope="col" className={cn(th, "pr-4 text-right")}>Cost</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {episodes.map((episode) => (
            <tr
              key={episode.id}
              onClick={() => onOpen(episode.id)}
              className={cn(
                "cursor-pointer transition-colors hover:bg-surface-2/70",
                episode.id === selectedId && "bg-accent-soft/30",
              )}
            >
              <td className="py-2 pl-4 pr-3">
                <button
                  type="button"
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpen(episode.id);
                  }}
                  aria-label={openLabel(episode, lookups)}
                  className="rounded-md text-left focus-visible:outline-offset-4"
                >
                  <TaskCell episode={episode} />
                </button>
              </td>
              <td className="whitespace-nowrap px-3 py-2"><ModelChip model={episode.model} /></td>
              <td className="whitespace-nowrap px-3 py-2 text-ink-2">{lookups.conditionLabel(episode.condition)}</td>
              <td className="px-3 py-2"><OutcomeBadge outcome={episode.outcome} /></td>
              <td className="px-3 py-2"><RunTrace episode={episode} /></td>
              <td className="whitespace-nowrap px-3 py-2 text-right tabular-nums text-ink-2">{seconds(episode.seconds)}</td>
              <td className="whitespace-nowrap py-2 pl-3 pr-4 text-right tabular-nums text-ink-2">{usd(episode.cost_usd)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/** Phones: one tappable card per episode. */
function EpisodeCards({ episodes, lookups, selectedId, onOpen }: EpisodeListProps) {
  return (
    <ul className="space-y-2 md:hidden">
      {episodes.map((episode) => (
        <li key={episode.id}>
          <button
            type="button"
            onClick={() => onOpen(episode.id)}
            aria-label={openLabel(episode, lookups)}
            className={cn(
              "flex w-full items-center gap-3 rounded-xl border border-border bg-surface p-3 text-left transition hover:border-border-strong",
              episode.id === selectedId && "ring-2 ring-accent/40",
            )}
          >
            <span className="min-w-0 flex-1 space-y-1.5">
              <span className="flex flex-wrap items-center justify-between gap-2">
                <TaskCell episode={episode} />
                <OutcomeBadge outcome={episode.outcome} />
              </span>
              <span className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-2">
                <ModelChip model={episode.model} className="text-xs" />
                <span>{lookups.conditionLabel(episode.condition)}</span>
                <RunTrace episode={episode} />
                <span className="tabular-nums">{seconds(episode.seconds)} · {usd(episode.cost_usd)}</span>
              </span>
            </span>
            <ChevronRight className="size-4 shrink-0 text-muted" aria-hidden />
          </button>
        </li>
      ))}
    </ul>
  );
}

export function EpisodeList(props: EpisodeListProps) {
  return (
    <>
      <EpisodeTable {...props} />
      <EpisodeCards {...props} />
    </>
  );
}
