// Explorer filter state. It lives in the URL (?run=v2&model=...) so any view
// can be shared as a link; this module is the pure logic behind it.
import type { Episode } from "../../lib/types";

export const ALL = "all";
export const FAILED = "failed"; // outcome filter: anything but passed

export type QueryPreset = "" | "untested" | "repairs";

export interface Filters {
  run: string;
  model: string;
  condition: string;
  outcome: string;
  task: string;
  q: string;
  preset: QueryPreset;
}

export const DEFAULT_FILTERS: Filters = {
  run: ALL,
  model: ALL,
  condition: ALL,
  outcome: ALL,
  task: ALL,
  q: "",
  preset: "",
};

const KEYS = Object.keys(DEFAULT_FILTERS) as (keyof Filters)[];

const asPreset = (value: string | null): QueryPreset =>
  value === "untested" || value === "repairs" ? value : "";

export function readFilters(params: URLSearchParams): Filters {
  const read = (key: keyof Filters) => params.get(key) ?? DEFAULT_FILTERS[key];
  return {
    run: read("run"),
    model: read("model"),
    condition: read("condition"),
    outcome: read("outcome"),
    task: read("task"),
    q: read("q"),
    preset: asPreset(params.get("preset")),
  };
}

/** A copy of `params` with `filters` written in; defaults are left out to keep links short. */
export function writeFilters(params: URLSearchParams, filters: Filters): URLSearchParams {
  const next = new URLSearchParams(params);
  for (const key of KEYS) {
    const value = filters[key];
    if (value === DEFAULT_FILTERS[key]) next.delete(key);
    else next.set(key, value);
  }
  return next;
}

export const isDefault = (filters: Filters) => KEYS.every((key) => filters[key] === DEFAULT_FILTERS[key]);

export const filtersKey = (filters: Filters) => KEYS.map((key) => filters[key]).join("|");

export const usesTools = (episode: Episode) => episode.condition !== "oneshot";

/** Tool condition, never called run_minilang, and failed. */
export const isUntestedFailure = (episode: Episode) =>
  usesTools(episode) && episode.runs.length === 0 && !episode.passed;

/** The first run failed, and the submitted program passed. */
export const isRepair = (episode: Episode) =>
  episode.passed && episode.runs.length > 0 && !episode.runs[0].ok;

const PRESET_TEST: Record<Exclude<QueryPreset, "">, (episode: Episode) => boolean> = {
  untested: isUntestedFailure,
  repairs: isRepair,
};

function matchesSearch(episode: Episode, query: string) {
  if (!query) return true;
  return [episode.task, episode.code ?? "", episode.error ?? ""].some((text) =>
    text.toLowerCase().includes(query),
  );
}

function matches(episode: Episode, filters: Filters, query: string) {
  if (filters.run !== ALL && episode.run !== filters.run) return false;
  if (filters.model !== ALL && episode.model !== filters.model) return false;
  if (filters.condition !== ALL && episode.condition !== filters.condition) return false;
  if (filters.task !== ALL && episode.task !== filters.task) return false;
  if (filters.outcome === FAILED && episode.passed) return false;
  if (filters.outcome !== ALL && filters.outcome !== FAILED && episode.outcome !== filters.outcome) {
    return false;
  }
  if (filters.preset && !PRESET_TEST[filters.preset](episode)) return false;
  return matchesSearch(episode, query);
}

export function applyFilters(episodes: Episode[], filters: Filters): Episode[] {
  const query = filters.q.trim().toLowerCase();
  return episodes.filter((episode) => matches(episode, filters, query));
}
