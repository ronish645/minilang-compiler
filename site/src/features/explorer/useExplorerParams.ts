import { useCallback, useMemo, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { DEFAULT_FILTERS, readFilters, writeFilters, type Filters } from "./filters";

const EPISODE_PARAM = "episode";

const withEpisode = (prev: URLSearchParams, id: string | null) => {
  const next = new URLSearchParams(prev);
  if (id) next.set(EPISODE_PARAM, id);
  else next.delete(EPISODE_PARAM);
  return next;
};

/**
 * Filters and the open episode, both stored in the URL so views are shareable.
 * Opening an episode pushes a history entry, so Back closes it; the close
 * button mirrors Back when it can, so history never gets a duplicate list entry.
 */
export function useExplorerParams() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const openedByPush = useRef(false);
  const filters = useMemo(() => readFilters(params), [params]);
  const episodeId = params.get(EPISODE_PARAM);

  const setFilters = useCallback(
    (next: Filters) => setParams((prev) => writeFilters(prev, next), { replace: true }),
    [setParams],
  );

  const updateFilters = useCallback(
    (patch: Partial<Filters>) => setFilters({ ...filters, ...patch }),
    [filters, setFilters],
  );

  const resetFilters = useCallback(() => setFilters(DEFAULT_FILTERS), [setFilters]);

  /** Open from the list: a new history entry. */
  const openEpisode = useCallback(
    (id: string) => {
      openedByPush.current = true;
      setParams((prev) => withEpisode(prev, id));
    },
    [setParams],
  );

  /** Prev/next inside the drawer: swap the episode in place. */
  const switchEpisode = useCallback(
    (id: string) => setParams((prev) => withEpisode(prev, id), { replace: true }),
    [setParams],
  );

  /** Close: go Back if we pushed the entry; for a deep link, just drop the param. */
  const closeEpisode = useCallback(() => {
    if (openedByPush.current) {
      openedByPush.current = false;
      navigate(-1);
    } else {
      setParams((prev) => withEpisode(prev, null), { replace: true });
    }
  }, [navigate, setParams]);

  return { filters, setFilters, updateFilters, resetFilters, episodeId, openEpisode, switchEpisode, closeEpisode };
}
