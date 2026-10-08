"""Summarize a benchmark run into markdown tables.

    python -m bench.report [run-name]      # default run-name: latest

Writes bench/results/<run-name>/REPORT.md and prints it.

Metrics
-------
pass rate     share of episodes whose submitted program printed exactly the
              expected output. Episodes that hit API errors are excluded.
repair rate   of the episodes whose *first* run failed, the share that still
              ended up passing. This isolates how useful the error feedback
              was, which is the point of comparing conditions.
first-run ok  share of tool episodes whose first run_minilang call succeeded.
tested        share of tool episodes where the model ran its code at least
              once before submitting (feedback can't help a model that
              never asks for it).
95% CI        Wilson score interval; with ~25 tasks per cell, differences
              smaller than the intervals are not meaningful.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

from bench.agent import Episode
from bench.config import ModelConfig, load_models
from bench.feedback import CONDITIONS, TOOL_CONDITIONS
from bench.grading import API_ERROR, PASSED
from bench.runner import RESULTS_DIR

Z_95 = 1.96


@dataclass(frozen=True)
class Rate:
    hits: int
    total: int

    @property
    def value(self) -> float | None:
        return self.hits / self.total if self.total else None

    def wilson_interval(self) -> tuple[float, float] | None:
        if not self.total:
            return None
        n, p = self.total, self.hits / self.total
        denominator = 1 + Z_95**2 / n
        center = (p + Z_95**2 / (2 * n)) / denominator
        margin = Z_95 * math.sqrt(p * (1 - p) / n + Z_95**2 / (4 * n**2)) / denominator
        return max(0.0, center - margin), min(1.0, center + margin)

    def format(self, with_ci: bool = False) -> str:
        if not self.total:
            return "–"
        text = f"{self.value:.0%} ({self.hits}/{self.total})"
        if with_ci:
            low, high = self.wilson_interval()
            text += f" [{low:.0%}–{high:.0%}]"
        return text


def rate(episodes: Iterable[Episode], predicate: Callable[[Episode], bool]) -> Rate:
    items = list(episodes)
    return Rate(sum(predicate(e) for e in items), len(items))


def pass_rate(episodes: Iterable[Episode]) -> Rate:
    return rate(episodes, lambda e: e.outcome == PASSED)


def repair_rate(episodes: Iterable[Episode]) -> Rate:
    first_run_failed = [e for e in episodes if e.runs and not e.runs[0].ok]
    return pass_rate(first_run_failed)


def first_run_ok(episodes: Iterable[Episode]) -> Rate:
    return rate([e for e in episodes if e.runs], lambda e: e.runs[0].ok)


def tested_rate(episodes: Iterable[Episode]) -> Rate:
    tool_episodes = [e for e in episodes if e.condition in TOOL_CONDITIONS]
    return rate(tool_episodes, lambda e: bool(e.runs))


def load_episodes(path: Path) -> list[Episode]:
    return [Episode.from_dict(json.loads(line)) for line in path.read_text().splitlines() if line]


def group(episodes: Iterable[Episode], *keys: str) -> dict[tuple, list[Episode]]:
    groups: dict[tuple, list[Episode]] = defaultdict(list)
    for e in episodes:
        groups[tuple(getattr(e, k) for k in keys)].append(e)
    return groups


def table(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join(lines)


def ordered_models(episodes: list[Episode], configs: dict[str, ModelConfig]) -> list[str]:
    present = {e.model_id for e in episodes}
    known = [m for m in configs if m in present]
    return known + sorted(present - set(known))


def section_pass_rates(by: dict, models: list[str], conditions: list[str]) -> str:
    rows = [[m] + [pass_rate(by.get((m, c), [])).format() for c in conditions] for m in models]
    return "## Pass rate by condition\n\n" + table(["Model", *conditions], rows)


def section_repair(by: dict, models: list[str], conditions: list[str]) -> str:
    tool_conditions = [c for c in conditions if c in TOOL_CONDITIONS]
    if not tool_conditions:
        return ""
    rows = [
        [m] + [repair_rate(by.get((m, c), [])).format(with_ci=True) for c in tool_conditions]
        for m in models
    ]
    pooled = [
        "**all models**",
        *[
            repair_rate([e for m in models for e in by.get((m, c), [])]).format(with_ci=True)
            for c in tool_conditions
        ],
    ]
    return (
        "## Repair rate: fixed after a failed first run\n\n"
        "Of the episodes whose first run failed, how many still passed. "
        "This is the effect of error-message quality.\n\n"
        + table(["Model", *tool_conditions], [*rows, pooled])
    )


def section_tiers(episodes: list[Episode], models: list[str]) -> str:
    tiers = sorted({e.tier for e in episodes})
    by = group(episodes, "model_id", "tier")
    rows = [[m] + [pass_rate(by.get((m, t), [])).format() for t in tiers] for m in models]
    return "## Pass rate by task tier (all conditions)\n\n" + table(
        ["Model", *[f"tier {t}" for t in tiers]], rows
    )


def section_cost(episodes: list[Episode], models: list[str], configs: dict) -> str:
    rows = []
    for m in models:
        mine = [e for e in episodes if e.model_id == m]
        cost = sum(configs[m].price.cost(e.usage) for e in mine) if m in configs else 0.0
        solved = sum(e.passed for e in mine)
        runs = [len(e.runs) for e in mine if e.condition in TOOL_CONDITIONS]
        rows.append(
            [
                m,
                tested_rate(mine).format(),
                first_run_ok(mine).format(),
                f"{sum(runs) / len(runs):.1f}" if runs else "–",
                f"{sum(e.seconds for e in mine) / len(mine):.1f}s",
                f"${cost:.3f}",
                f"${cost / solved:.4f}" if solved else "–",
            ]
        )
    headers = [
        "Model",
        "Tested first",
        "First run ok",
        "Avg runs",
        "Avg time",
        "Total cost",
        "Cost per solve",
    ]
    return "## Efficiency and cost\n\n" + table(headers, rows)


def section_outcomes(episodes: list[Episode], models: list[str]) -> str:
    outcomes = sorted({e.outcome for e in episodes})
    by = group(episodes, "model_id", "outcome")
    rows = [[m] + [str(len(by.get((m, o), []))) for o in outcomes] for m in models]
    return "## Outcomes\n\n" + table(["Model", *outcomes], rows)


def section_hardest(episodes: list[Episode]) -> str:
    by_task = group(episodes, "task_id")
    ranked = sorted(by_task.items(), key=lambda kv: pass_rate(kv[1]).value or 0)[:8]
    rows = [[task, str(eps[0].tier), pass_rate(eps).format()] for (task,), eps in ranked]
    return "## Hardest tasks\n\n" + table(["Task", "Tier", "Pass rate"], rows)


def build_report(all_episodes: list[Episode], run_name: str) -> str:
    configs = {m.id: m for m in load_models()}
    api_errors = [e for e in all_episodes if e.outcome == API_ERROR]
    episodes = [e for e in all_episodes if e.outcome != API_ERROR]
    models = ordered_models(episodes, configs)
    conditions = [c for c in CONDITIONS if any(e.condition == c for e in episodes)]
    by = group(episodes, "model_id", "condition")
    samples = len({e.sample for e in episodes})

    header = (
        f"# MiniLang LLM benchmark: `{run_name}`\n\n"
        f"{len(episodes)} graded episodes · {len(models)} models · "
        f"{len({e.task_id for e in episodes})} tasks · {samples} sample(s) per task"
    )
    if api_errors:
        header += f" · {len(api_errors)} API-error episodes excluded"
    sections = [
        header,
        section_pass_rates(by, models, conditions),
        section_repair(by, models, conditions),
        section_tiers(episodes, models),
        section_cost(episodes, models, configs),
        section_outcomes(episodes, models),
        section_hardest(episodes),
    ]
    return "\n\n".join(s for s in sections if s) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    run_name = args[0] if args else "latest"
    path = RESULTS_DIR / run_name / "episodes.jsonl"
    if not path.exists():
        print(f"no results at {path}; run python -m bench.runner first", file=sys.stderr)
        return 1
    report = build_report(load_episodes(path), run_name)
    (path.parent / "REPORT.md").write_text(report)
    print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
