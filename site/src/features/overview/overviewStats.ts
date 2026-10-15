// Numbers shown on the Overview page, computed from summary.json so the copy
// can never drift from the data. Rates are always per run: the two runs used
// different task tiers and language versions, so they are never pooled.
import { sortRunsOldestFirst } from "../../lib/runs";
import type { ModelStats, RateData, Summary } from "../../lib/types";

export interface Tally {
  hits: number;
  total: number;
  rate: number | null;
}

const sumRates = (rates: RateData[]): Tally => {
  const hits = rates.reduce((acc, rate) => acc + rate.hits, 0);
  const total = rates.reduce((acc, rate) => acc + rate.total, 0);
  return { hits, total, rate: total === 0 ? null : hits / total };
};

const isHosted = (summary: Summary, model: string) =>
  summary.models.some((info) => info.id === model && info.provider !== "ollama");

const hostedRows = (summary: Summary, run: string): ModelStats[] =>
  summary.model_stats.filter((row) => row.run === run && isHosted(summary, row.model));

/** Run ids, oldest first (by date, not JSON order). The first is the main v2 run. */
export const runIds = (summary: Summary) => sortRunsOldestFirst(summary.runs).map((run) => run.id);

export const runShortTitle = (summary: Summary, run: string) =>
  summary.runs.find((info) => info.id === run)?.title.split(" · ")[0] ?? run;

/** Hosted (API) models in one run: passed / graded episodes. */
export const hostedPass = (summary: Summary, run: string) =>
  sumRates(hostedRows(summary, run).map((row) => row.pass));

/** Hosted models' first `run_minilang` call succeeded (the ceiling). */
export const hostedFirstRunOk = (summary: Summary, run: string) =>
  sumRates(hostedRows(summary, run).map((row) => row.first_run_ok));

/** The local model's repairs in one run: a failed run fixed before submitting (the floor). */
export function localRepairs(summary: Summary, run: string) {
  const local = summary.models.find((model) => model.provider === "ollama");
  const row = summary.model_stats.find((stats) => stats.run === run && stats.model === local?.id);
  return row ? { model: row.model, ...row.repair } : null;
}

/** Hosted failures in one run, and the model responsible for most of them. */
export function hostedFailures(summary: Summary, run: string) {
  const rows = hostedRows(summary, run).map((row) => ({
    row,
    failed: row.pass.total - row.pass.hits,
  }));
  const total = rows.reduce((acc, item) => acc + item.failed, 0);
  const worst = [...rows].sort((a, b) => b.failed - a.failed)[0];
  return { total, count: worst?.failed ?? 0, model: worst?.row.model ?? "", tested: worst?.row.tested };
}

export interface CostPerSolve {
  model: string;
  perSolve: number;
  passRate: number | null;
}

/** Cost per passing episode for each hosted model in one run, cheapest first. */
export const costPerSolve = (summary: Summary, run: string): CostPerSolve[] =>
  hostedRows(summary, run)
    .filter((row) => row.cost_per_solve != null && row.cost_per_solve > 0)
    .map((row) => ({ model: row.model, perSolve: row.cost_per_solve ?? 0, passRate: row.pass.value }))
    .sort((a, b) => a.perSolve - b.perSolve);
