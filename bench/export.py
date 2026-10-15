"""Export benchmark results as JSON for the showcase site.

    python -m bench.export [out-dir]      # default: site/public/data

Writes three files:

summary.json    pre-computed metrics for the charts (pass, repair and tested
                rates with 95% Wilson intervals, cost, outcomes, error patterns)
episodes.json   every graded episode, slimmed down for the episode explorer
tasks.json      task prompts and expected output (reference solutions stay hidden)

The metrics reuse bench.report, so the site and REPORT.md can't disagree.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bench.agent import Episode
from bench.config import ModelConfig, load_models
from bench.feedback import CONDITIONS, TOOL_CONDITIONS
from bench.grading import API_ERROR
from bench.report import (
    Rate,
    first_run_ok,
    group,
    load_episodes,
    pass_rate,
    repair_rate,
    tested_rate,
)
from bench.runner import RESULTS_DIR
from bench.tasks import load_tasks

DEFAULT_OUT_DIR = Path(__file__).resolve().parent.parent / "site" / "public" / "data"
TOP_ERROR_PATTERNS = 8  # per model and run


@dataclass(frozen=True)
class RunInfo:
    id: str
    date: str
    title: str
    description: str


# Runs shown on the site, oldest first. Each used a different spec version,
# so the site keeps them apart instead of pooling them.
RUNS = (
    RunInfo(
        "v2",
        "2026-10-08",
        "Tiers 1–4 · language v1",
        "32 small tasks, including spec traps that punish JavaScript and Python habits.",
    ),
    RunInfo(
        "v21-tier5",
        "2026-10-14",
        "Tier 5 · language v2.1",
        "10 multi-step array and string programs, plus the fix-it hint condition.",
    ),
)

MODEL_LABELS = {
    "claude-haiku": "Claude Haiku 5.5",
    "claude-sonnet": "Claude Sonnet 5.5",
    "gpt-luna": "GPT-6 Luna",
    "gpt-sol": "GPT-6.1 Sol",
    "qwen-3b-local": "Qwen 2.5 3B (local)",
}

CONDITION_INFO = {
    "oneshot": ("One-shot", "No tools: the model writes the program once, without running it."),
    "opaque": ("Opaque", "Failures only say: Error: the program failed."),
    "message": ("Message", "The error message, with no location."),
    "diagnostic": ("Diagnostic", "Stage, line and column, the source line and a caret."),
    "hint": ("Hint", "Every error with source snippets, plus fix-it hints."),
}

# "Syntax error at line 3, col 9: " -> ""; quoted names -> '…'
POSITION_PREFIX = re.compile(r"^\w+ error(?: at line \d+, col \d+)?: ")
QUOTED_NAME = re.compile(r"'[A-Za-z_][A-Za-z0-9_]*'")


def rate_json(r: Rate) -> dict[str, Any]:
    interval = r.wilson_interval()
    low, high = interval if interval else (None, None)
    return {"hits": r.hits, "total": r.total, "value": r.value, "low": low, "high": high}


def error_pattern(error: str | None) -> str | None:
    """Group errors by kind: drop the position and anonymize identifiers."""
    if not error:
        return None
    first_line = POSITION_PREFIX.sub("", error.strip().splitlines()[0])
    return QUOTED_NAME.sub("'…'", first_line)


def episode_cost(episode: Episode, configs: dict[str, ModelConfig]) -> float:
    config = configs.get(episode.model_id)
    return config.price.cost(episode.usage) if config else 0.0


def graded(episodes: list[Episode]) -> list[Episode]:
    """Episodes that count toward rates (infrastructure failures are excluded)."""
    return [e for e in episodes if e.outcome != API_ERROR]


def model_stats(run: str, model: str, mine: list[Episode], configs: dict) -> dict[str, Any]:
    cost = sum(episode_cost(e, configs) for e in mine)
    solved = sum(e.passed for e in mine)
    tool_runs = [len(e.runs) for e in mine if e.condition in TOOL_CONDITIONS]
    return {
        "run": run,
        "model": model,
        "episodes": len(mine),
        "pass": rate_json(pass_rate(mine)),
        "tested": rate_json(tested_rate(mine)),
        "first_run_ok": rate_json(first_run_ok(mine)),
        "repair": rate_json(repair_rate(mine)),
        "cost_usd": cost,
        "cost_per_solve": cost / solved if solved else None,
        "avg_seconds": sum(e.seconds for e in mine) / len(mine),
        "avg_runs": sum(tool_runs) / len(tool_runs) if tool_runs else None,
        "output_tokens": sum(e.usage.output_tokens for e in mine),
        "outcomes": dict(Counter(e.outcome for e in mine)),
    }


def run_sections(run: str, episodes: list[Episode], configs: dict) -> dict[str, list]:
    """Every chart's rows for one run."""
    by_model = group(episodes, "model_id")
    cells = [
        {"run": run, "model": m, "condition": c, "pass": rate_json(pass_rate(eps)),
         "repair": rate_json(repair_rate(eps))}
        for (m, c), eps in group(episodes, "model_id", "condition").items()
    ]  # fmt: skip
    tiers = [
        {"run": run, "model": m, "tier": t, "pass": rate_json(pass_rate(eps))}
        for (m, t), eps in group(episodes, "model_id", "tier").items()
    ]
    repair = [
        {"run": run, "condition": c, "rate": rate_json(repair_rate(eps))}
        for (c,), eps in group(episodes, "condition").items()
        if c in TOOL_CONDITIONS
    ]
    patterns = []
    for (m,), eps in by_model.items():
        counts = Counter(p for p in map(error_pattern, (e.error for e in eps)) if p)
        patterns += [
            {"run": run, "model": m, "pattern": p, "count": n}
            for p, n in counts.most_common(TOP_ERROR_PATTERNS)
        ]
    return {
        "cells": cells,
        "tiers": tiers,
        "repair": repair,
        "error_patterns": patterns,
        "model_stats": [model_stats(run, m, eps, configs) for (m,), eps in by_model.items()],
    }


def build_summary(runs: dict[str, list[Episode]]) -> dict[str, Any]:
    configs = {m.id: m for m in load_models()}
    run_info = {r.id: r for r in RUNS}
    sections: dict[str, list] = {
        k: [] for k in ("cells", "tiers", "repair", "error_patterns", "model_stats")
    }
    for run, episodes in runs.items():
        for key, rows in run_sections(run, graded(episodes), configs).items():
            sections[key] += rows

    every = [e for eps in runs.values() for e in eps]
    return {
        "runs": [
            {**vars(run_info[r]), "episodes": len(eps)}
            if r in run_info
            else {"id": r, "episodes": len(eps)}
            for r, eps in runs.items()
        ],  # fmt: skip
        "models": [
            {
                "id": m.id,
                "label": MODEL_LABELS.get(m.id, m.id),
                "provider": m.provider,
                "tier": m.tier,
                "price_in": m.price.input,
                "price_out": m.price.output,
            }
            for m in configs.values()
        ],  # fmt: skip
        "conditions": [
            {
                "id": c,
                "label": CONDITION_INFO[c][0],
                "description": CONDITION_INFO[c][1],
                "uses_tools": c in TOOL_CONDITIONS,
            }
            for c in CONDITIONS
        ],  # fmt: skip
        "totals": {
            "episodes": len(every),
            "passed": sum(e.passed for e in every),
            "models": len({e.model_id for e in every}),
            "tasks": len({e.task_id for e in every}),
            "cost_usd": sum(episode_cost(e, configs) for e in every),
        },
        **sections,
    }


def build_episodes(runs: dict[str, list[Episode]]) -> list[dict[str, Any]]:
    configs = {m.id: m for m in load_models()}
    rows = []
    for run, episodes in runs.items():
        for e in episodes:
            rows.append(
                {
                    "id": f"{run}/{e.model_id}/{e.task_id}/{e.condition}/{e.sample}",
                    "run": run,
                    "model": e.model_id,
                    "task": e.task_id,
                    "tier": e.tier,
                    "condition": e.condition,
                    "outcome": e.outcome,
                    "passed": e.passed,
                    "code": e.code,
                    "output": e.output,
                    "error": e.error,
                    "runs": [{"ok": r.ok, "stage": r.stage} for r in e.runs],
                    "turns": e.model_turns,
                    "seconds": e.seconds,
                    "cost_usd": episode_cost(e, configs),
                }
            )
    return rows


def build_tasks() -> list[dict[str, Any]]:
    return [
        {"id": t.id, "tier": t.tier, "prompt": t.prompt, "expected": list(t.expected)}
        for t in load_tasks()
    ]


def load_runs(results_dir: Path = RESULTS_DIR) -> dict[str, list[Episode]]:
    runs = {}
    for info in RUNS:
        path = results_dir / info.id / "episodes.jsonl"
        if not path.exists():
            raise FileNotFoundError(f"missing results for run '{info.id}': {path}")
        runs[info.id] = load_episodes(path)
    return runs


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False) + "\n")


def export(out_dir: Path = DEFAULT_OUT_DIR) -> None:
    runs = load_runs()
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "summary.json", build_summary(runs))
    write_json(out_dir / "episodes.json", build_episodes(runs))
    write_json(out_dir / "tasks.json", build_tasks())


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    out_dir = Path(args[0]) if args else DEFAULT_OUT_DIR
    export(out_dir)
    print(f"wrote summary.json, episodes.json and tasks.json to {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
