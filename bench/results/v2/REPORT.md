# MiniLang LLM benchmark: `v2`

640 graded episodes · 5 models · 32 tasks · 1 sample(s) per task

## Pass rate by condition

| Model | oneshot | opaque | message | diagnostic |
|---|---|---|---|---|
| claude-haiku | 100% (32/32) | 100% (32/32) | 100% (32/32) | 100% (32/32) |
| claude-sonnet | 100% (32/32) | 97% (31/32) | 97% (31/32) | 97% (31/32) |
| gpt-luna | 100% (32/32) | 100% (32/32) | 100% (32/32) | 100% (32/32) |
| gpt-sol | 100% (32/32) | 100% (32/32) | 100% (32/32) | 100% (32/32) |
| qwen-3b-local | 28% (9/32) | 31% (10/32) | 38% (12/32) | 31% (10/32) |

## Repair rate: fixed after a failed first run

Of the episodes whose first run failed, how many still passed. This is the effect of error-message quality.

| Model | opaque | message | diagnostic |
|---|---|---|---|
| claude-haiku | 100% (2/2) [34%–100%] | 100% (1/1) [21%–100%] | 100% (1/1) [21%–100%] |
| claude-sonnet | 100% (2/2) [34%–100%] | 100% (3/3) [44%–100%] | 100% (3/3) [44%–100%] |
| gpt-luna | 100% (1/1) [21%–100%] | – | – |
| gpt-sol | – | – | 100% (1/1) [21%–100%] |
| qwen-3b-local | 10% (1/10) [2%–40%] | 0% (0/13) [0%–23%] | 0% (0/10) [0%–28%] |
| **all models** | 40% (6/15) [20%–64%] | 24% (4/17) [10%–47%] | 33% (5/15) [15%–58%] |

## Pass rate by task tier (all conditions)

| Model | tier 1 | tier 2 | tier 3 | tier 4 |
|---|---|---|---|---|
| claude-haiku | 100% (32/32) | 100% (40/40) | 100% (28/28) | 100% (28/28) |
| claude-sonnet | 100% (32/32) | 100% (40/40) | 89% (25/28) | 100% (28/28) |
| gpt-luna | 100% (32/32) | 100% (40/40) | 100% (28/28) | 100% (28/28) |
| gpt-sol | 100% (32/32) | 100% (40/40) | 100% (28/28) | 100% (28/28) |
| qwen-3b-local | 56% (18/32) | 40% (16/40) | 25% (7/28) | 0% (0/28) |

## Efficiency and cost

| Model | Tested first | First run ok | Avg runs | Avg time | Total cost | Cost per solve |
|---|---|---|---|---|---|---|
| claude-haiku | 97% (93/96) | 96% (89/93) | 1.0 | 3.4s | $0.067 | $0.0005 |
| claude-sonnet | 35% (34/96) | 76% (26/34) | 0.4 | 3.1s | $0.869 | $0.0070 |
| gpt-luna | 100% (96/96) | 99% (95/96) | 1.0 | 4.1s | $0.020 | $0.0002 |
| gpt-sol | 100% (96/96) | 99% (95/96) | 1.0 | 5.7s | $0.325 | $0.0025 |
| qwen-3b-local | 73% (70/96) | 53% (37/70) | 1.1 | 15.9s | $0.000 | $0.0000 |

## Outcomes

| Model | compile_error | no_code | passed | runtime_error | wrong_output |
|---|---|---|---|---|---|
| claude-haiku | 0 | 0 | 128 | 0 | 0 |
| claude-sonnet | 3 | 0 | 125 | 0 | 0 |
| gpt-luna | 0 | 0 | 128 | 0 | 0 |
| gpt-sol | 0 | 0 | 128 | 0 | 0 |
| qwen-3b-local | 58 | 14 | 41 | 1 | 14 |

## Hardest tasks

| Task | Tier | Pass rate |
|---|---|---|
| digit_sum | 3 | 65% (13/20) |
| countdown | 1 | 80% (16/20) |
| gcd | 2 | 80% (16/20) |
| primes | 2 | 80% (16/20) |
| fibonacci | 2 | 80% (16/20) |
| stars | 2 | 80% (16/20) |
| reverse_number | 3 | 80% (16/20) |
| nth_prime | 4 | 80% (16/20) |
