import type { RunInfo } from "./types";

/** Runs in chronological order; never rely on the order of summary.runs in the JSON. */
export const sortRunsOldestFirst = (runs: RunInfo[]): RunInfo[] =>
  [...runs].sort((a, b) => a.date.localeCompare(b.date));

export const sortRunsNewestFirst = (runs: RunInfo[]): RunInfo[] =>
  sortRunsOldestFirst(runs).reverse();

/** One name for a run everywhere on the site, e.g. "Tiers 1–4 · language v1". */
export const runLabel = (run: RunInfo): string => run.title;

/** A compact label with the date, for run pickers: "Tier 5 · v2.1 (Oct 14)". */
export const runShortLabel = (run: RunInfo): string => {
  const date = new Date(`${run.date}T00:00:00`).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
  });
  return `${run.title.replace("language ", "")} (${date})`;
};
