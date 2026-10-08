"""ChatSession for OpenAI-compatible Chat Completions APIs.

Used for local models served by Ollama, which exposes this API at
http://localhost:11434/v1. (OpenAI's own reasoning models reject tools on
this endpoint unless reasoning is turned off, so they use
``responses_session.py`` instead.)
"""

from __future__ import annotations

import json
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

FINISH_REASONS = {
    "stop": STOP_END,
    "tool_calls": STOP_TOOL,
    "length": STOP_LENGTH,
    "content_filter": STOP_REFUSAL,
}


def to_openai_tool(spec: ToolSpec) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": spec.name,
            "description": spec.description,
            "parameters": spec.parameters,
            "strict": True,
        },
    }


def parse_arguments(raw: str | None) -> dict[str, Any]:
    """Tool arguments arrive as a JSON string; small models sometimes emit bad JSON."""
    try:
        parsed = json.loads(raw or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


class ChatCompletionsSession:
    def __init__(
        self,
        client: openai.OpenAI,
        model: str,
        system: str,
        tools: list[ToolSpec],
        extra: dict[str, Any] | None = None,
    ):
        self.client = client
        self.model = model
        self.tools = [to_openai_tool(t) for t in tools]
        self.extra = extra or {}
        self.messages: list[dict[str, Any]] = [{"role": "system", "content": system}]

    def send_user(self, text: str) -> Turn:
        self.messages.append({"role": "user", "content": text})
        return self._complete()

    def send_tool_results(self, results: list[ToolResult]) -> Turn:
        for r in results:
            # OpenAI has no is_error flag; the content itself says it failed.
            self.messages.append({"role": "tool", "tool_call_id": r.call_id, "content": r.content})
        return self._complete()

    def _complete(self) -> Turn:
        params: dict[str, Any] = {"model": self.model, "messages": self.messages, **self.extra}
        if self.tools:
            params["tools"] = self.tools
        try:
            response = self.client.chat.completions.create(**params)
        except openai.APIStatusError as error:
            raise ProviderError(f"chat completions {error.status_code}: {error.message}") from error
        except openai.APIConnectionError as error:
            raise ProviderError(f"chat completions connection error: {error}") from error

        choice = response.choices[0]
        message = choice.message
        calls = message.tool_calls or []
        assistant: dict[str, Any] = {"role": "assistant", "content": message.content or ""}
        if calls:
            assistant["tool_calls"] = [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {"name": c.function.name, "arguments": c.function.arguments},
                }
                for c in calls
            ]
        self.messages.append(assistant)

        stop = FINISH_REASONS.get(choice.finish_reason, STOP_END)
        if getattr(message, "refusal", None):
            stop = STOP_REFUSAL
        return Turn(
            text=message.content or "",
            tool_calls=[
                ToolCall(c.id, c.function.name, parse_arguments(c.function.arguments))
                for c in calls
            ],
            stop=stop,
            usage=usage_from(response.usage),
        )


def usage_from(usage: Any) -> Usage:
    if usage is None:
        return Usage()
    details = getattr(usage, "prompt_tokens_details", None)
    cached = (getattr(details, "cached_tokens", None) or 0) if details else 0
    return Usage(
        input_tokens=usage.prompt_tokens - cached,
        output_tokens=usage.completion_tokens,
        cache_read_tokens=cached,
    )
