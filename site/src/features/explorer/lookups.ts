// Label and task lookups built once from summary.json and tasks.json.
import { byModelOrder, CONDITION_ORDER } from "../../lib/models";
import { sortRunsOldestFirst } from "../../lib/runs";
import type { Summary, Task } from "../../lib/types";

export interface Lookups {
  runs: { id: string; label: string; date: string }[];
  models: { id: string; label: string }[];
  conditions: { id: string; label: string; usesTools: boolean }[];
  tasks: Task[]; // ordered by tier, then id
  runLabel: (id: string) => string;
  conditionLabel: (id: string) => string;
  task: (id: string) => Task | undefined;
}

const conditionRank = (id: string) => {
  const index = CONDITION_ORDER.indexOf(id as (typeof CONDITION_ORDER)[number]);
  return index === -1 ? CONDITION_ORDER.length : index;
};

export function buildLookups(summary: Summary, tasks: Task[]): Lookups {
  const runs = sortRunsOldestFirst(summary.runs).map((run) => ({
    id: run.id,
    label: run.title.split(" · ")[0] ?? run.id,
    date: run.date,
  }));
  const models = [...summary.models]
    .sort((a, b) => byModelOrder(a.id, b.id))
    .map((model) => ({ id: model.id, label: model.label }));
  const conditions = [...summary.conditions]
    .sort((a, b) => conditionRank(a.id) - conditionRank(b.id))
    .map((condition) => ({ id: condition.id, label: condition.label, usesTools: condition.uses_tools }));
  const orderedTasks = [...tasks].sort((a, b) => a.tier - b.tier || a.id.localeCompare(b.id));
  const taskById = new Map(tasks.map((task) => [task.id, task]));
  const runById = new Map(runs.map((run) => [run.id, run.label]));
  const conditionById = new Map(conditions.map((condition) => [condition.id, condition.label]));

  return {
    runs,
    models,
    conditions,
    tasks: orderedTasks,
    runLabel: (id) => runById.get(id) ?? id,
    conditionLabel: (id) => conditionById.get(id) ?? id,
    task: (id) => taskById.get(id),
  };
}
