"""Grade a submitted program: run it and compare its output exactly."""

from __future__ import annotations

import re
from dataclasses import dataclass

from bench.tasks import Task
from minilang.pipeline import run_source

# Episode outcomes. Only PASSED counts as a success.
PASSED = "passed"
WRONG_OUTPUT = "wrong_output"
COMPILE_ERROR = "compile_error"
RUNTIME_ERROR = "runtime_error"
NO_CODE = "no_code"  # the model never produced a program
REFUSAL = "refusal"
TURN_LIMIT = "turn_limit"  # ran out of model turns without submitting
API_ERROR = "api_error"  # infrastructure failure; excluded from pass rates

FENCED_BLOCK = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)


@dataclass(frozen=True)
class Grade:
    outcome: str
    output: tuple[str, ...] = ()
    error: str | None = None

    @property
    def passed(self) -> bool:
        return self.outcome == PASSED


def extract_code(text: str) -> str | None:
    """Return the last fenced code block in a model's reply."""
    blocks = FENCED_BLOCK.findall(text)
    return blocks[-1] if blocks else None


def grade(code: str | None, task: Task) -> Grade:
    if not code or not code.strip():
        return Grade(NO_CODE)
    result = run_source(code)
    output = tuple(result.output)
    if not result.ok:
        outcome = COMPILE_ERROR if result.is_compile_error else RUNTIME_ERROR
        return Grade(outcome, output, result.error["message"])
    return Grade(PASSED if output == task.expected else WRONG_OUTPUT, output)
