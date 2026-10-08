# MiniLang LLM Benchmark

**Question:** can a language model write correct code in a programming language it has never seen, given only the language specification? And when its code fails, **how much does the quality of the compiler's error message help it recover?**

MiniLang was written for this project, so it can't be in any model's training data. Models have to learn it from [`docs/LANGUAGE_SPEC.md`](../docs/LANGUAGE_SPEC.md), which is placed in the system prompt.

## How an episode works

```
system prompt: spec + rules          user: task + exact expected output
          │                                     │
          └──────────────▶  model  ◀────────────┘
                              │  run_minilang(code)
                              ▼
                     MiniLang compiler ──▶ feedback (depends on condition)
                              │
                   ... repeat (max 5 runs, 8 model turns) ...
                              │  submit_solution(code)
                              ▼
               graded: run the program, compare output exactly
```

The model sees the expected output, as it would with a test case. The reference solution stays hidden. The grader is deterministic: the program's printed lines must match exactly.

## Conditions (the experimental variable)

| Condition | Tools | What the model sees when its code fails |
|---|---|---|
| `oneshot` | none | n/a: it writes the program once, blind |
| `opaque` | run + submit | `Error: the program failed.` |
| `message` | run + submit | `Error: variable 'y' used before declaration` |
| `diagnostic` | run + submit | Stage, `file:line:col`, the source line and a `^` caret, plus output printed before a runtime error |

Successful runs look identical in every condition: the printed output.

## Tasks

32 tasks in [`tasks.yaml`](tasks.yaml), each with a hidden reference solution. [`tests/bench/test_tasks_and_config.py`](../tests/bench/test_tasks_and_config.py) runs every reference solution, so an unsolvable task can't silently cap the scores.

| Tier | Count | What it tests |
|---|---|---|
| 1 | 8 | Basics: loops, conditionals, functions |
| 2 | 10 | Classic small algorithms |
| 3 | 7 | **Spec traps** that punish habits from JS and Python: no `break`, `/` always returns a float (and a variable's type is fixed), `&&` doesn't short-circuit |
| 4 | 7 | Traps combined: no int-to-string conversion means one-line output like `Sum = 5050` needs hand-built digit-to-text code |

Tier 4 was added after the first run showed frontier models solving almost all of tiers 1–3. They solved tier 4 too (see [Lessons](#lessons-from-building-it)).

## Models

Configured in [`models.yaml`](models.yaml). Tiers are matched on price so each comparison is fair:

| Tier | Anthropic | OpenAI | $ per 1M tokens (in / out) |
|---|---|---|---|
| small | Claude Haiku 5.5 | GPT-6 Luna | 0.10 / 0.50 |
| mid | Claude Sonnet 5.5 | GPT-6.1 Sol | 2 / 10 |
| local | Qwen 2.5 3B via Ollama | | free |

All hosted models run with reasoning on at `medium` effort. Server-side refusal fallbacks are deliberately off, so every answer comes from the model being measured.

## Metrics

- **Pass rate:** share of episodes whose submitted program printed exactly the expected output. Episodes that hit an API error are excluded and reported separately.
- **Repair rate:** of the episodes whose *first* run failed, the share that still passed. This is the cleanest measure of how useful the feedback was.
- **Tested first:** share of tool episodes where the model ran its code before submitting.
- **Cost per solve:** total spend divided by tasks solved, computed from token usage with prompt-cache pricing.
- Rates come with **Wilson 95% confidence intervals**. With 32 tasks per cell, small differences are noise, and the report shows the intervals so nobody over-reads them.

## Running it

```bash
pip install -e ".[bench]"
cp .env.example .env                      # add ANTHROPIC_API_KEY / OPENAI_API_KEY
python -m bench.runner --dry-run          # plan and cost estimate, no API calls
python -m bench.runner --run-name v2      # run everything (cached episodes are free)
python -m bench.report v2                 # writes bench/results/v2/REPORT.md
```

Useful filters: `--models claude-haiku gpt-luna`, `--tiers 3 4`, `--conditions oneshot diagnostic`, `--samples 3`.

## Implementation notes

- **One loop, three APIs.** [`agent.py`](agent.py) talks to a small `ChatSession` protocol ([`llm/base.py`](llm/base.py)). Adapters translate to the Anthropic Messages API, the OpenAI **Responses** API, and Chat Completions (used for Ollama).
- **Provider-native history.** Each adapter keeps the conversation in its provider's own format and appends the raw response, so Claude's thinking blocks and OpenAI's reasoning items go back unchanged on the next turn.
- **Why the Responses API for OpenAI:** GPT-6 models reject function tools combined with reasoning on `/v1/chat/completions`. Turning reasoning off would have made the comparison with Claude unfair.
- **Caching at two levels.** Prompt caching cuts the cost of resending the about 3K-token spec every turn. An on-disk episode cache (keyed by a hash of model, task, condition, prompt and limits) makes interrupted or repeated runs free.
- **Safety.** Model-written code runs inside the interpreter's step, call-depth and output limits, so an infinite loop costs one error message, not a hung benchmark.

## Lessons from building it

1. **Ceiling effects are stubborn.** Frontier models saturated tiers 1–3, so there were almost no failures to repair. A harder tier 4 was saturated too (112/112, even one-shot). Making small tasks harder didn't move the ceiling. Measuring repair on frontier models needs a different kind of task (larger programs) or a different population (mid-size models).
2. **Not every model uses its tools.** The first failures were all one model submitting confident, untested code that fell into the float-division trap. Feedback quality only matters if the model asks for feedback, hence the *Tested first* metric.
3. **"OpenAI-compatible" isn't one API.** The same model needed a different endpoint once tools and reasoning were combined.

## Results (run `v2`, 2026-10-08)

640 graded episodes: 5 models × 32 tasks × 4 conditions × 1 sample, about **$1.30** in API cost. Full tables: [`results/v2/REPORT.md`](results/v2/REPORT.md). Every episode, including the submitted code, is in [`results/v2/episodes.jsonl`](results/v2/episodes.jsonl).

| Model | Pass rate (all conditions) | One-shot | Tested before submitting | Cost per solve |
|---|---|---|---|---|
| Claude Haiku 5.5 | **100%** (128/128) | 32/32 | 97% | $0.0005 |
| GPT-6 Luna | **100%** (128/128) | 32/32 | 100% | $0.0002 |
| GPT-6.1 Sol | **100%** (128/128) | 32/32 | 100% | $0.0025 |
| Claude Sonnet 5.5 | 98% (125/128) | 32/32 | **35%** | $0.0070 |
| Qwen 2.5 3B (local) | 32% (41/128) | 9/32 | 73% | free |

### Findings

1. **Frontier models learned the language from the spec alone.** The four hosted models passed 509 of 512 episodes, and all 128 one-shot episodes, where they wrote each program once without being able to run it. That includes tier 3–4 tasks built to punish JavaScript/Python habits.
2. **Error-message quality made no measurable difference.** Pooled repair rates were 40% (opaque), 24% (message) and 33% (diagnostic), with heavily overlapping 95% intervals (roughly 10–64%). It's a null result, and the reasons are informative:
   - Hosted models rarely failed a first run (14 times in 384 tool episodes) and fixed **every one**, even with the opaque "the program failed" feedback. For them, any signal was enough.
   - The 3B model rarely fixed anything (1 of 33), whatever the feedback. Its errors were mostly JavaScript/Python syntax it carried over (`array[i]`, `.method()`, `for i in`, `break`, `?:`), and it re-ran code in only 22 of its 70 tool episodes. Better messages can't help a model that doesn't iterate or can't act on them.
3. **Every hosted-model failure was an untested submission.** Claude Sonnet ran its code before submitting in only 35% of tool episodes, against 97–100% for the others. All 3 of its failures were confident, untested programs that hit the float-division trap. Its testing habit, not its capability, cost it the perfect score, while costing about 14× more per solve than Claude Haiku.
4. **The cheapest models were the best value.** GPT-6 Luna and Claude Haiku matched or beat their mid-tier siblings at a fraction of the cost per solve.

### Limitations

- One sample per task and condition. The intervals are wide, and the null result on feedback quality is "no detectable effect", not "no effect".
- The tasks are small programs. Larger tasks would produce more first-run failures and more room to measure repair.
- The missing middle: models between 3B and frontier scale (for example 7–14B open models) are where error quality is most likely to matter. That's the natural next experiment.
