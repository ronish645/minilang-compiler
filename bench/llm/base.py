"""Provider-neutral chat interface used by the agent loop.

Each provider formats tool calls differently (Anthropic: ``tool_use`` /
``tool_result`` content blocks; OpenAI: ``tool_calls`` / ``role: "tool"``
messages). A ``ChatSession`` hides that: it owns the provider-native message
history and exchanges plain ``Turn`` / ``ToolResult`` objects with the agent.

Keeping history provider-native (instead of translating to a common format and
back) matters for Claude: its responses can contain thinking blocks that must
be sent back unchanged on the next request.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for the tool's arguments


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class ToolResult:
    call_id: str
    content: str
    is_error: bool = False


@dataclass(frozen=True)
class Usage:
    input_tokens: int = 0  # uncached input, billed at the full input price
    output_tokens: int = 0
    cache_read_tokens: int = 0  # input served from the prompt cache (~0.1x price)
    cache_write_tokens: int = 0  # input written to the prompt cache (~1.25x price)

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            self.input_tokens + other.input_tokens,
            self.output_tokens + other.output_tokens,
            self.cache_read_tokens + other.cache_read_tokens,
            self.cache_write_tokens + other.cache_write_tokens,
        )


# Normalized reasons a model turn ended.
STOP_END = "end"  # finished speaking
STOP_TOOL = "tool"  # wants tool results
STOP_LENGTH = "length"  # hit the output-token cap
STOP_REFUSAL = "refusal"  # declined by safety systems


@dataclass(frozen=True)
class Turn:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop: str = STOP_END
    usage: Usage = field(default_factory=Usage)


class ChatSession(Protocol):
    def send_user(self, text: str) -> Turn: ...

    def send_tool_results(self, results: list[ToolResult]) -> Turn: ...


class ProviderError(Exception):
    """An API call failed (network, auth, rate limit after retries, ...)."""
