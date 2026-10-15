// Shapes of the JSON written by `python -m bench.export` (see bench/export.py).

export interface RateData {
  hits: number;
  total: number;
  value: number | null; // hits / total, or null when total is 0
  low: number | null; // 95% Wilson interval
  high: number | null;
}

export interface RunInfo {
  id: string; // "v2" | "v21-tier5"
  date: string;
  title: string;
  description: string;
  episodes: number;
}

export interface ModelInfo {
  id: string;
  label: string;
  provider: "anthropic" | "openai" | "ollama";
  tier: "small" | "mid" | "local";
  price_in: number; // USD per 1M tokens
  price_out: number;
}

export interface ConditionInfo {
  id: string; // "oneshot" | "opaque" | "message" | "diagnostic" | "hint"
  label: string;
  description: string;
  uses_tools: boolean;
}

export interface Cell {
  run: string;
  model: string;
  condition: string;
  pass: RateData;
  repair: RateData;
}

export interface TierRow {
  run: string;
  model: string;
  tier: number;
  pass: RateData;
}

export interface RepairRow {
  run: string;
  condition: string;
  rate: RateData; // pooled across models
}

export interface ErrorPattern {
  run: string;
  model: string;
  pattern: string;
  count: number;
}

export type Outcome =
  | "passed"
  | "wrong_output"
  | "compile_error"
  | "runtime_error"
  | "no_code"
  | "refusal"
  | "turn_limit"
  | "api_error";

export interface ModelStats {
  run: string;
  model: string;
  episodes: number;
  pass: RateData;
  tested: RateData; // tool episodes where the model ran its code before submitting
  first_run_ok: RateData;
  repair: RateData;
  cost_usd: number;
  cost_per_solve: number | null;
  avg_seconds: number;
  avg_runs: number | null;
  output_tokens: number;
  outcomes: Partial<Record<Outcome, number>>;
}

export interface Summary {
  runs: RunInfo[];
  models: ModelInfo[];
  conditions: ConditionInfo[];
  totals: { episodes: number; passed: number; models: number; tasks: number; cost_usd: number };
  cells: Cell[];
  tiers: TierRow[];
  repair: RepairRow[];
  error_patterns: ErrorPattern[];
  model_stats: ModelStats[];
}

export interface EpisodeRun {
  ok: boolean;
  stage: string | null; // error stage when not ok
}

export interface Episode {
  id: string;
  run: string;
  model: string;
  task: string;
  tier: number;
  condition: string;
  outcome: Outcome;
  passed: boolean;
  code: string | null;
  output: string[];
  error: string | null;
  runs: EpisodeRun[];
  turns: number;
  seconds: number;
  cost_usd: number;
}

export interface Task {
  id: string;
  tier: number;
  prompt: string;
  expected: string[];
}
