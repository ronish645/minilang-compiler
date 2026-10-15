# MiniLang LLM benchmark: `v21-tier5`

200 graded episodes · 4 models · 10 tasks · 1 sample(s) per task

## Pass rate by condition

| Model | oneshot | opaque | message | diagnostic | hint |
|---|---|---|---|---|---|
| claude-haiku | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| claude-sonnet | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| gpt-luna | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |
| gpt-sol | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) | 100% (10/10) |

## Repair rate: fixed after a failed first run

Of the episodes whose first run failed, how many still passed. This is the effect of error-message quality.

| Model | opaque | message | diagnostic | hint |
|---|---|---|---|---|
| claude-haiku | – | – | – | – |
| claude-sonnet | – | – | – | – |
| gpt-luna | – | – | – | – |
| gpt-sol | – | – | – | – |
| **all models** | – | – | – | – |

## Pass rate by task tier (all conditions)

| Model | tier 5 |
|---|---|
| claude-haiku | 100% (50/50) |
| claude-sonnet | 100% (50/50) |
| gpt-luna | 100% (50/50) |
| gpt-sol | 100% (50/50) |

## Efficiency and cost

| Model | Tested first | First run ok | Avg runs | Avg time | Total cost | Cost per solve |
|---|---|---|---|---|---|---|
| claude-haiku | 100% (40/40) | 100% (40/40) | 1.0 | 3.8s | $0.035 | $0.0007 |
| claude-sonnet | 50% (20/40) | 100% (20/20) | 0.5 | 2.9s | $0.463 | $0.0093 |
| gpt-luna | 100% (40/40) | 100% (40/40) | 1.0 | 5.9s | $0.016 | $0.0003 |
| gpt-sol | 100% (40/40) | 100% (40/40) | 1.0 | 6.0s | $0.237 | $0.0047 |

## Outcomes

| Model | passed |
|---|---|
| claude-haiku | 50 |
| claude-sonnet | 50 |
| gpt-luna | 50 |
| gpt-sol | 50 |

## Hardest tasks

| Task | Tier | Pass rate |
|---|---|---|
| bubble_sort | 5 | 100% (20/20) |
| run_length | 5 | 100% (20/20) |
| binary_search | 5 | 100% (20/20) |
| reverse_words | 5 | 100% (20/20) |
| matrix_multiply | 5 | 100% (20/20) |
| sieve | 5 | 100% (20/20) |
| caesar | 5 | 100% (20/20) |
| balanced_brackets | 5 | 100% (20/20) |
