"""Benchmark tasks: what the model is asked to write, and how it is graded."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from bench.config import BENCH_DIR

DEFAULT_TASKS_FILE = BENCH_DIR / "tasks.yaml"
VALID_TIERS = (1, 2, 3, 4)


@dataclass(frozen=True)
class Task:
    id: str
    tier: int
    prompt: str
    expected: tuple[str, ...]  # exact output lines
    reference: str  # hidden known-good solution

    def user_message(self) -> str:
        expected = "\n".join(self.expected)
        return (
            f"Task: {self.prompt}\n\n"
            "Your program must print exactly this output:\n"
            f"```\n{expected}\n```"
        )


def parse_task(raw: dict) -> Task:
    missing = {"id", "tier", "prompt", "expected", "reference"} - raw.keys()
    if missing:
        raise ValueError(f"task {raw.get('id', raw)!r} is missing {sorted(missing)}")
    if raw["tier"] not in VALID_TIERS:
        raise ValueError(f"task {raw['id']!r}: tier must be one of {VALID_TIERS}")
    return Task(
        id=raw["id"],
        tier=raw["tier"],
        prompt=" ".join(raw["prompt"].split()),
        expected=tuple(raw["expected"].splitlines()),
        reference=raw["reference"],
    )


def load_tasks(path: Path = DEFAULT_TASKS_FILE) -> list[Task]:
    tasks = [parse_task(raw) for raw in yaml.safe_load(path.read_text())["tasks"]]
    ids = [t.id for t in tasks]
    duplicates = {i for i in ids if ids.count(i) > 1}
    if duplicates:
        raise ValueError(f"duplicate task ids in {path.name}: {sorted(duplicates)}")
    return tasks
