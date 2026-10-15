# MiniLang LLM benchmark: `v21-tier5`

250 graded episodes · 5 models · 10 tasks · 1 sample(s) per task

## Pass rate by condition

| Model | oneshot | opaque | message | diagnostic | hint |
|---|---|---|---|---|---|
| claude-haiku | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| claude-sonnet | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| gpt-luna | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| gpt-sol | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| qwen-3b-local | 0% (0/10) | 0% (0/10) | 10% (1/10) | 0% (0/10) | 10% (1/10) |

## Repair rate: fixed after a failed first run

Of the episodes whose first run failed, how many still passed. This is the effect of error-message quality.

| Model | opaque | message | diagnostic | hint |
|---|---|---|---|---|
| claude-haiku | – | – | – | – |
| claude-sonnet | – | – | – | – |
| gpt-luna | – | – | – | – |
| gpt-sol | – | – | – | – |
| qwen-3b-local | 0% (0/2) [0%–66%] | 0% (0/5) [0%–43%] | 0% (0/7) [0%–35%] | 0% (0/1) [0%–79%] |
| **all models** | 0% (0/2) [0%–66%] | 0% (0/5) [0%–43%] | 0% (0/7) [0%–35%] | 0% (0/1) [0%–79%] |

## Pass rate by task tier (all conditions)

| Model | tier 5 |
|---|---|
| claude-haiku | 100% (50/50) |
| claude-sonnet | 100% (50/50) |
| gpt-luna | 100% (50/50) |
| gpt-sol | 100% (50/50) |
| qwen-3b-local | 4% (2/50) |

## Efficiency and cost

| Model | Tested first | First run ok | Avg runs | Avg time | Total cost | Cost per solve |
|---|---|---|---|---|---|---|
| claude-haiku | 100% (40/40) | 100% (40/40) | 1.0 | 3.8s | $0.035 | $0.0007 |
| claude-sonnet | 50% (20/40) | 100% (20/20) | 0.5 | 2.9s | $0.463 | $0.0093 |
| gpt-luna | 100% (40/40) | 100% (40/40) | 1.0 | 5.9s | $0.016 | $0.0003 |
| gpt-sol | 100% (40/40) | 100% (40/40) | 1.0 | 6.0s | $0.237 | $0.0047 |
| qwen-3b-local | 42% (17/40) | 12% (2/17) | 0.8 | 28.0s | $0.000 | $0.0000 |

## Outcomes

| Model | compile_error | no_code | passed | wrong_output |
|---|---|---|---|---|
| claude-haiku | 0 | 0 | 50 | 0 |
| claude-sonnet | 0 | 0 | 50 | 0 |
| gpt-luna | 0 | 0 | 50 | 0 |
| gpt-sol | 0 | 0 | 50 | 0 |
| qwen-3b-local | 28 | 17 | 2 | 3 |

## Hardest tasks

| Task | Tier | Pass rate |
|---|---|---|
| binary_search | 5 | 80% (20/25) |
| run_length | 5 | 80% (20/25) |
| reverse_words | 5 | 80% (20/25) |
| balanced_brackets | 5 | 80% (20/25) |
| matrix_multiply | 5 | 80% (20/25) |
| sieve | 5 | 80% (20/25) |
| caesar | 5 | 80% (20/25) |
| anagrams | 5 | 80% (20/25) |
