"""The agent loop: one model attempts one task under one feedback condition.

task prompt ──▶ model ──▶ run_minilang(code) ──▶ compiler ──▶ feedback ──┐
                 ▲                                                       │
                 └───────────────────────────────────────────────────────┘
                 ... until the model calls submit_solution(code), which is graded.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any

from bench.feedback import ONESHOT, format_run_result
from bench.grading import (
    API_ERROR,
    NO_CODE,
    REFUSAL,
    TURN_LIMIT,
    Grade,
    extract_code,
    grade,
)
from bench.llm.base import STOP_REFUSAL, ProviderError, ToolCall, ToolResult, Turn, Usage
from bench.llm.registry import SessionFactory
from bench.prompts import RUN_TOOL, SUBMIT_TOOL, TOOLS, system_prompt
from bench.tasks import Task
from minilang.pipeline import run_source


@dataclass(frozen=True)
class AgentLimits:
    max_runs: int = 5  # run_minilang calls per episode
    max_model_turns: int = 8  # model responses per episode


@dataclass(frozen=True)
class RunRecord:
    ok: bool
    stage: str | None  # error stage when not ok


@dataclass
class Episode:
    model_id: str
    task_id: str
    tier: int
    condition: str
    sample: int
    outcome: str = NO_CODE
    code: str | None = None
    output: list[str] = field(default_factory=list)
    error: str | None = None
    runs: list[RunRecord] = field(default_factory=list)
    model_turns: int = 0
    usage: Usage = field(default_factory=Usage)
    seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return self.outcome == "passed"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["passed"] = self.passed
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Episode:
        fields = {k: v for k, v in data.items() if k != "passed"}
        fields["runs"] = [RunRecord(**r) for r in fields.get("runs", [])]
        fields["usage"] = Usage(**fields.get("usage", {}))
        return cls(**fields)


class EpisodeRunner:
    """Holds the per-episode state while the loop runs."""

    def __init__(self, episode: Episode, task: Task, limits: AgentLimits):
        self.episode = episode
        self.task = task
        self.limits = limits
        self.submitted: str | None = None
        self.last_run_code: str | None = None

    def record_turn(self, turn: Turn) -> Turn:
        self.episode.model_turns += 1
        self.episode.usage = self.episode.usage + turn.usage
        return turn

    def handle_call(self, call: ToolCall) -> ToolResult:
        code = call.arguments.get("code")
        if not isinstance(code, str):
            return ToolResult(call.id, "Error: the 'code' argument must be a string.", True)
        if call.name == SUBMIT_TOOL:
            self.submitted = code
            return ToolResult(call.id, "Submitted.")
        if call.name != RUN_TOOL:
            return ToolResult(call.id, f"Error: unknown tool {call.name!r}.", True)
        if len(self.episode.runs) >= self.limits.max_runs:
            message = f"Run limit reached. Call {SUBMIT_TOOL} with your best program now."
            return ToolResult(call.id, message, True)

        self.last_run_code = code
        result = run_source(code)
        stage = None if result.ok else result.error["stage"]
        self.episode.runs.append(RunRecord(result.ok, stage))
        return ToolResult(call.id, format_run_result(result, self.episode.condition), not result.ok)

    def finish(self, code: str | None, outcome: str | None = None) -> Episode:
        if outcome is None:
            graded: Grade = grade(code, self.task)
            outcome = graded.outcome
            self.episode.output = list(graded.output)
            self.episode.error = graded.error
        self.episode.code = code
        self.episode.outcome = outcome
        return self.episode


def run_tool_loop(runner: EpisodeRunner, session, task: Task) -> Episode:
    turn = runner.record_turn(session.send_user(task.user_message()))
    while True:
        if turn.stop == STOP_REFUSAL:
            return runner.finish(None, REFUSAL)
        if not turn.tool_calls:
            # The model stopped without submitting: grade a code block from its
            # reply, or else the last program it ran.
            return runner.finish(extract_code(turn.text) or runner.last_run_code)

        results = [runner.handle_call(call) for call in turn.tool_calls]
        if runner.submitted is not None:
            return runner.finish(runner.submitted)
        if runner.episode.model_turns >= runner.limits.max_model_turns:
            return runner.finish(runner.last_run_code, TURN_LIMIT)
        turn = runner.record_turn(session.send_tool_results(results))


def run_episode(
    factory: SessionFactory,
    model_id: str,
    task: Task,
    condition: str,
    spec: str,
    sample: int = 0,
    limits: AgentLimits | None = None,
) -> Episode:
    limits = limits or AgentLimits()
    episode = Episode(model_id, task.id, task.tier, condition, sample)
    runner = EpisodeRunner(episode, task, limits)
    uses_tools = condition != ONESHOT
    started = time.monotonic()
    try:
        session = factory(
            system_prompt(spec, uses_tools, limits.max_runs), TOOLS if uses_tools else []
        )
        if uses_tools:
            run_tool_loop(runner, session, task)
        else:
            turn = runner.record_turn(session.send_user(task.user_message()))
            if turn.stop == STOP_REFUSAL:
                runner.finish(None, REFUSAL)
            else:
                runner.finish(extract_code(turn.text))
    except ProviderError as error:
        episode.outcome = API_ERROR
        episode.error = str(error)
    episode.seconds = round(time.monotonic() - started, 2)
    return episode
