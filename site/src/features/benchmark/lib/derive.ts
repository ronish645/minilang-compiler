// Pure helpers that slice summary.json down to one run. Runs are never pooled.
import { CONDITION_ORDER, MODEL_ORDER } from "../../../lib/models";
import type { Cell, ConditionInfo, ModelStats, RateData, RunInfo, Summary } from "../../../lib/types";

export interface Rate {
  hits: number;
  total: number;
  value: number | null;
}

const orderIndex = (list: readonly string[], id: string) => {
  const index = list.indexOf(id);
  return index === -1 ? list.length : index;
};

/** Runs, newest first. */
export const runsNewestFirst = (summary: Summary): RunInfo[] =>
  [...summary.runs].sort((a, b) => b.date.localeCompare(a.date));

export const findRun = (summary: Summary, runId: string): RunInfo | undefined =>
  summary.runs.find((run) => run.id === runId);

export const isLocalModel = (summary: Summary, modelId: string) =>
  summary.models.find((model) => model.id === modelId)?.tier === "local";

/** Per-model stats for one run, in the site-wide model order. */
export const statsForRun = (summary: Summary, runId: string): ModelStats[] =>
  summary.model_stats
    .filter((row) => row.run === runId)
    .sort((a, b) => orderIndex(MODEL_ORDER, a.model) - orderIndex(MODEL_ORDER, b.model));

export const modelsForRun = (summary: Summary, runId: string): string[] =>
  statsForRun(summary, runId).map((row) => row.model);

/** The conditions that actually ran in this run, in the canonical order. */
export const conditionsForRun = (summary: Summary, runId: string): ConditionInfo[] => {
  const present = new Set(summary.cells.filter((c) => c.run === runId).map((c) => c.condition));
  return summary.conditions
    .filter((condition) => present.has(condition.id))
    .sort((a, b) => orderIndex(CONDITION_ORDER, a.id) - orderIndex(CONDITION_ORDER, b.id));
};

export const findCell = (
  summary: Summary,
  runId: string,
  model: string,
  condition: string,
): Cell | undefined =>
  summary.cells.find((c) => c.run === runId && c.model === model && c.condition === condition);

/** Add up hits and totals (all from the same run). */
export const poolRates = (rates: RateData[]): Rate => {
  const hits = rates.reduce((sum, rate) => sum + rate.hits, 0);
  const total = rates.reduce((sum, rate) => sum + rate.total, 0);
  return { hits, total, value: total > 0 ? hits / total : null };
};

export interface HostedSplit {
  hosted: ModelStats[];
  local: ModelStats[];
}

export const splitHosted = (summary: Summary, stats: ModelStats[]): HostedSplit => ({
  hosted: stats.filter((row) => !isLocalModel(summary, row.model)),
  local: stats.filter((row) => isLocalModel(summary, row.model)),
});

/** Tasks per run, derived from the grid: episodes / (models × conditions). */
export const tasksInRun = (summary: Summary, runId: string): number => {
  const models = modelsForRun(summary, runId).length;
  const conditions = conditionsForRun(summary, runId).length;
  const run = findRun(summary, runId);
  if (!run || models === 0 || conditions === 0) return 0;
  return Math.round(run.episodes / (models * conditions));
};

export const runCost = (stats: ModelStats[]) => stats.reduce((sum, row) => sum + row.cost_usd, 0);

export const minBy = <T>(items: T[], score: (item: T) => number): T | undefined =>
  items.reduce<T | undefined>(
    (best, item) => (best === undefined || score(item) < score(best) ? item : best),
    undefined,
  );

export const maxBy = <T>(items: T[], score: (item: T) => number): T | undefined =>
  minBy(items, (item) => -score(item));
