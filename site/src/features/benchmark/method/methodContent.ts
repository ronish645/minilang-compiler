// Static methodology copy, taken from bench/README.md.

export const TIERS = [
  { tier: 1, tasks: 8, what: "Basics: loops, conditionals, functions." },
  { tier: 2, tasks: 10, what: "Classic small algorithms." },
  {
    tier: 3,
    tasks: 7,
    what: "Spec traps that punish JavaScript and Python habits, such as / always returning a float.",
  },
  {
    tier: 4,
    tasks: 7,
    what: "Traps combined, e.g. one-line output that needs hand-built digit-to-text code.",
  },
  {
    tier: 5,
    tasks: 10,
    what: "Array and string programs: sorting, binary search, sieve, matrix multiply, bracket matching.",
  },
] as const;

export const METRICS = [
  {
    term: "Pass rate",
    definition: "Share of episodes whose submitted program printed exactly the expected output.",
  },
  {
    term: "Repair rate",
    definition:
      "Of the episodes whose first run failed, the share that still passed. The cleanest measure of whether feedback helped.",
  },
  {
    term: "Tested first",
    definition: "Share of tool episodes where the model ran its code at least once before submitting.",
  },
  {
    term: "Cost per solve",
    definition: "Total API spend divided by tasks solved, from token usage with prompt-cache pricing.",
  },
  {
    term: "Wilson 95% interval",
    definition:
      "A confidence interval for a rate that stays sensible with small samples and with rates near 0% or 100%. Wide intervals mean: don't over-read the difference.",
  },
] as const;

export const LIMITATIONS = [
  "One sample per task and condition, so intervals are wide. The feedback result is \"no detectable effect\", not \"no effect\".",
  "The tasks are small programs. Larger tasks would produce more first-run failures and more room to measure repair.",
  "The missing middle: no model between 3B and frontier scale (7–32B) yet. That is where error quality is most likely to matter, and it is the next experiment.",
  "In the tiers 1–4 run, Ollama's default 4,096-token context cut off part of the spec for Qwen, so that score understates it. Tier 5 used a 16K window.",
  "The two runs used different spec versions (v1 and v2.1) and are never pooled.",
] as const;
