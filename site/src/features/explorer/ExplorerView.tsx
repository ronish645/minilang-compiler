import { SearchX } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { Container } from "../../components/layout/Page";
import { Button } from "../../components/ui/Button";
import { ErrorState, Skeleton } from "../../components/ui/StateViews";
import { useEpisodes, useSummary, useTasks } from "../../lib/data";
import type { Episode, Outcome, Summary, Task } from "../../lib/types";
import { Drawer } from "./detail/Drawer";
import { DETAIL_TITLE_ID, EpisodeDetail } from "./detail/EpisodeDetail";
import { EpisodeList } from "./EpisodeList";
import { FilterBar } from "./FilterBar";
import { applyFilters, filtersKey } from "./filters";
import { buildLookups } from "./lookups";
import { PresetChips } from "./PresetChips";
import { useExplorerParams } from "./useExplorerParams";

const PAGE_SIZE = 25;

interface ReadyProps {
  summary: Summary;
  episodes: Episode[];
  tasks: Task[];
}

/** "Show more" paging that resets whenever the filters change. */
function usePaging(key: string) {
  const [state, setState] = useState({ key, limit: PAGE_SIZE });
  const limit = state.key === key ? state.limit : PAGE_SIZE;
  const ensure = useCallback((count: number) => setState({ key, limit: Math.max(limit, count) }), [key, limit]);
  return { limit, ensure };
}

function EmptyResult({ onReset }: { onReset: () => void }) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border-strong px-6 py-14 text-center">
      <SearchX className="size-6 text-muted" aria-hidden />
      <p className="font-medium text-ink">No episodes match these filters</p>
      <Button size="sm" onClick={onReset}>Reset filters</Button>
    </div>
  );
}

function ExplorerReady({ summary, episodes, tasks }: ReadyProps) {
  const lookups = useMemo(() => buildLookups(summary, tasks), [summary, tasks]);
  const byId = useMemo(() => new Map(episodes.map((episode) => [episode.id, episode])), [episodes]);
  const outcomes = useMemo(() => [...new Set(episodes.map((e) => e.outcome))] as Outcome[], [episodes]);
  const { filters, setFilters, updateFilters, resetFilters, episodeId, openEpisode, switchEpisode, closeEpisode } =
    useExplorerParams();
  const filtered = useMemo(() => applyFilters(episodes, filters), [episodes, filters]);
  const { limit, ensure } = usePaging(filtersKey(filters));

  const selected = episodeId ? (byId.get(episodeId) ?? null) : null;
  const index = selected ? filtered.findIndex((episode) => episode.id === selected.id) : -1;

  const step = (delta: number) => {
    const next = filtered[index + delta];
    if (!next) return;
    ensure(index + delta + 1); // keep the list in sync with the drawer
    switchEpisode(next.id);
  };

  return (
    <Container className="space-y-6 py-8 sm:py-10">
      <PresetChips filters={filters} episodes={episodes} onSelect={setFilters} />
      <FilterBar
        filters={filters}
        onChange={updateFilters}
        onReset={resetFilters}
        lookups={lookups}
        outcomes={outcomes}
        shown={filtered.length}
        total={episodes.length}
      />
      {filtered.length === 0 ? (
        <EmptyResult onReset={resetFilters} />
      ) : (
        <EpisodeList episodes={filtered.slice(0, limit)} lookups={lookups} selectedId={selected?.id ?? null} onOpen={openEpisode} />
      )}
      {filtered.length > limit && (
        <div className="flex flex-col items-center gap-2">
          <Button onClick={() => ensure(limit + PAGE_SIZE)}>Show {Math.min(PAGE_SIZE, filtered.length - limit)} more</Button>
          <p className="text-xs text-muted">Showing {limit} of {filtered.length}</p>
        </div>
      )}
      {selected && (
        <Drawer labelledBy={DETAIL_TITLE_ID} onClose={closeEpisode}>
          <EpisodeDetail
            episode={selected}
            lookups={lookups}
            position={index === -1 ? null : { index, total: filtered.length }}
            onPrev={() => step(-1)}
            onNext={() => step(1)}
            onClose={closeEpisode}
          />
        </Drawer>
      )}
    </Container>
  );
}

export function ExplorerView() {
  const summary = useSummary();
  const episodes = useEpisodes();
  const tasks = useTasks();
  const failed = [summary, episodes, tasks].find((state) => state.status === "error");

  if (failed?.status === "error") {
    return <Container className="py-10"><ErrorState message={failed.message} /></Container>;
  }
  if (summary.status !== "ready" || episodes.status !== "ready" || tasks.status !== "ready") {
    return (
      <Container className="py-10">
        <div className="space-y-4" aria-busy="true" aria-label="Loading episodes">
          <Skeleton className="h-8 w-2/3" />
          <Skeleton className="h-20 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </Container>
    );
  }
  return <ExplorerReady summary={summary.data} episodes={episodes.data} tasks={tasks.data} />;
}
