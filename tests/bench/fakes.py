"""A scripted stand-in for a real model, so the agent loop can be tested offline."""

from __future__ import annotations

from bench.llm.base import STOP_END, STOP_TOOL, ToolCall, ToolResult, Turn, Usage


def run(code: str, call_id: str = "c1") -> Turn:
    return Turn("", [ToolCall(call_id, "run_minilang", {"code": code})], STOP_TOOL, Usage(10, 5))


def submit(code: str, call_id: str = "s1") -> Turn:
    return Turn("", [ToolCall(call_id, "submit_solution", {"code": code})], STOP_TOOL, Usage(10, 5))


def reply(text: str) -> Turn:
    return Turn(text, [], STOP_END, Usage(10, 5))


class FakeSession:
    def __init__(self, turns: list[Turn]):
        self.turns = list(turns)
        self.system: str | None = None
        self.tools: list = []
        self.user_messages: list[str] = []
        self.tool_results: list[list[ToolResult]] = []

    def send_user(self, text: str) -> Turn:
        self.user_messages.append(text)
        return self.turns.pop(0)

    def send_tool_results(self, results: list[ToolResult]) -> Turn:
        self.tool_results.append(results)
        return self.turns.pop(0)


def factory_for(session: FakeSession):
    def factory(system, tools):
        session.system = system
        session.tools = tools
        return session

    return factory
