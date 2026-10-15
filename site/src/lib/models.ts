// Each model keeps one color everywhere on the site (color follows the entity,
// never its rank). Slots come from the validated categorical palette.

export const MODEL_ORDER = [
  "claude-haiku",
  "claude-sonnet",
  "gpt-luna",
  "gpt-sol",
  "qwen-3b-local",
] as const;

export const MODEL_COLOR: Record<string, string> = {
  "claude-haiku": "var(--series-1)",
  "claude-sonnet": "var(--series-2)",
  "gpt-luna": "var(--series-3)",
  "gpt-sol": "var(--series-4)",
  "qwen-3b-local": "var(--series-5)",
};

export const MODEL_SHORT: Record<string, string> = {
  "claude-haiku": "Haiku 5.5",
  "claude-sonnet": "Sonnet 5.5",
  "gpt-luna": "GPT-6 Luna",
  "gpt-sol": "GPT-6.1 Sol",
  "qwen-3b-local": "Qwen 3B",
};

export const CONDITION_ORDER = ["oneshot", "opaque", "message", "diagnostic", "hint"] as const;

export const OUTCOME_LABEL: Record<string, string> = {
  passed: "Passed",
  wrong_output: "Wrong output",
  compile_error: "Compile error",
  runtime_error: "Runtime error",
  no_code: "No code",
  refusal: "Refusal",
  turn_limit: "Turn limit",
  api_error: "API error",
};

export const modelColor = (id: string) => MODEL_COLOR[id] ?? "var(--muted)";
export const modelShort = (id: string) => MODEL_SHORT[id] ?? id;
export const byModelOrder = (a: string, b: string) =>
  MODEL_ORDER.indexOf(a as never) - MODEL_ORDER.indexOf(b as never);
