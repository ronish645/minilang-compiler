"""ChatSession for OpenAI models via the Responses API.

OpenAI's reasoning models only accept function tools together with
reasoning on /v1/responses, not /v1/chat/completions. Reasoning stays on
here so the comparison with Claude (adaptive thinking) is fair.
"""

from __future__ import annotations

from typing import Any

import openai

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
from bench.llm.chat_completions_session import parse_arguments

MAX_OUTPUT_TOKENS = 16_000
INCOMPLETE_REASONS = {"max_output_tokens": STOP_LENGTH, "content_filter": STOP_REFUSAL}


def to_responses_tool(spec: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "name": spec.name,
        "description": spec.description,
        "parameters": spec.parameters,
        "strict": True,
    }


class ResponsesSession:
    def __init__(
        self,
        client: openai.OpenAI,
        model: str,
        system: str,
        tools: list[ToolSpec],
        effort: str | None = None,
        extra: dict[str, Any] | None = None,
    ):
        self.client = client
        self.model = model
        self.system = system
        self.tools = [to_responses_tool(t) for t in tools]
        self.effort = effort
        self.extra = extra or {}
        self.items: list[Any] = []  # the conversation, as Responses API input items

    def send_user(self, text: str) -> Turn:
        self.items.append({"role": "user", "content": text})
        return self._complete()

    def send_tool_results(self, results: list[ToolResult]) -> Turn:
        for r in results:
            self.items.append(
                {"type": "function_call_output", "call_id": r.call_id, "output": r.content}
            )
        return self._complete()

    def _complete(self) -> Turn:
        params: dict[str, Any] = {
            "model": self.model,
            "instructions": self.system,
            "input": self.items,
            "max_output_tokens": MAX_OUTPUT_TOKENS,
            **self.extra,
        }
        if self.tools:
            params["tools"] = self.tools
        if self.effort:
            params["reasoning"] = {"effort": self.effort}
        try:
            response = self.client.responses.create(**params)
        except openai.APIStatusError as error:
            raise ProviderError(f"openai {error.status_code}: {error.message}") from error
        except openai.APIConnectionError as error:
            raise ProviderError(f"openai connection error: {error}") from error

        # Output items (reasoning, messages, function calls) go back as input
        # next turn so the model keeps its own context.
        self.items.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        return Turn(
            text=response.output_text or "",
            tool_calls=[ToolCall(c.call_id, c.name, parse_arguments(c.arguments)) for c in calls],
            stop=stop_reason(response, bool(calls)),
            usage=usage_from(response.usage),
        )


def stop_reason(response: Any, has_calls: bool) -> str:
    if response.status == "incomplete":
        reason = getattr(response.incomplete_details, "reason", None)
        return INCOMPLETE_REASONS.get(reason, STOP_LENGTH)
    for item in response.output:
        if item.type == "message" and any(c.type == "refusal" for c in item.content):
            return STOP_REFUSAL
    return STOP_TOOL if has_calls else STOP_END


def usage_from(usage: Any) -> Usage:
    if usage is None:
        return Usage()
    details = getattr(usage, "input_tokens_details", None)
    cached = (getattr(details, "cached_tokens", None) or 0) if details else 0
    return Usage(
        input_tokens=usage.input_tokens - cached,
        output_tokens=usage.output_tokens,
        cache_read_tokens=cached,
    )
