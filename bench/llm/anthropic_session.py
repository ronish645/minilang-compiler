"""ChatSession for Claude via the Anthropic Messages API (manual tool loop)."""

from __future__ import annotations

from typing import Any

import anthropic

from bench.llm.base import (
    STOP_END,
    STOP_LENGTH,
    STOP_REFUSAL,
    STOP_TOOL,
    ProviderError,
    ToolCall,
    ToolResult,
    ToolSpec,
    Turn,
    Usage,
)

MAX_OUTPUT_TOKENS = 16_000  # non-streaming; tasks need far less
STOP_REASONS = {
    "end_turn": STOP_END,
    "tool_use": STOP_TOOL,
    "max_tokens": STOP_LENGTH,
    "refusal": STOP_REFUSAL,
}


def to_anthropic_tool(spec: ToolSpec) -> dict[str, Any]:
    # strict: the API guarantees tool inputs match the schema.
    return {
        "name": spec.name,
        "description": spec.description,
        "input_schema": spec.parameters,
        "strict": True,
    }


class AnthropicSession:
    def __init__(
        self,
        client: anthropic.Anthropic,
        model: str,
        system: str,
        tools: list[ToolSpec],
        effort: str | None = None,
        extra: dict[str, Any] | None = None,
    ):
        self.client = client
        self.model = model
        self.system = system
        self.tools = [to_anthropic_tool(t) for t in tools]
        self.effort = effort
        self.extra = extra or {}
        self.messages: list[dict[str, Any]] = []

    def send_user(self, text: str) -> Turn:
        self.messages.append({"role": "user", "content": text})
        return self._complete()

    def send_tool_results(self, results: list[ToolResult]) -> Turn:
        # All results for one assistant turn go back in a single user message.
        blocks = [
            {
                "type": "tool_result",
                "tool_use_id": r.call_id,
                "content": r.content,
                "is_error": r.is_error,
            }
            for r in results
        ]
        self.messages.append({"role": "user", "content": blocks})
        return self._complete()

    def _request_params(self) -> dict[str, Any]:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": MAX_OUTPUT_TOKENS,
            "system": self.system,
            "messages": self.messages,
            # Auto-cache the growing prefix: the spec in the system prompt and
            # earlier turns are re-sent on every step of the loop.
            "cache_control": {"type": "ephemeral"},
            **self.extra,
        }
        if self.tools:
            params["tools"] = self.tools
        if self.effort:
            params["output_config"] = {"effort": self.effort}
        return params

    def _complete(self) -> Turn:
        try:
            response = self.client.messages.create(**self._request_params())
        except anthropic.APIStatusError as error:
            raise ProviderError(
                f"anthropic {error.status_code} (request {error.request_id}): {error.message}"
            ) from error
        except anthropic.APIConnectionError as error:
            raise ProviderError(f"anthropic connection error: {error}") from error

        # Send the full content back next time: it may contain thinking blocks
        # that must be returned unchanged.
        self.messages.append({"role": "assistant", "content": response.content})
        return Turn(
            text="".join(b.text for b in response.content if b.type == "text"),
            tool_calls=[
                ToolCall(b.id, b.name, dict(b.input))
                for b in response.content
                if b.type == "tool_use"
            ],
            stop=STOP_REASONS.get(response.stop_reason, STOP_END),
            usage=Usage(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                cache_read_tokens=response.usage.cache_read_input_tokens or 0,
                cache_write_tokens=response.usage.cache_creation_input_tokens or 0,
            ),
        )
