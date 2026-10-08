"""Build the right ChatSession for a configured model."""

from __future__ import annotations

import os
from collections.abc import Callable
from functools import cache

from bench.config import DEFAULT_OLLAMA_BASE_URL, ModelConfig
from bench.llm.base import ChatSession, ToolSpec

# The SDKs retry 408/409/429/5xx and connection errors with backoff.
API_MAX_RETRIES = 4

SessionFactory = Callable[[str, list[ToolSpec]], ChatSession]


@cache
def anthropic_client():
    import anthropic

    return anthropic.Anthropic(max_retries=API_MAX_RETRIES)


@cache
def openai_client(base_url: str | None = None, api_key: str | None = None):
    import openai

    return openai.OpenAI(base_url=base_url, api_key=api_key, max_retries=API_MAX_RETRIES)


def session_factory(model: ModelConfig) -> SessionFactory:
    """Return a function that starts a fresh conversation with ``model``."""
    if model.provider == "anthropic":
        from bench.llm.anthropic_session import AnthropicSession

        return lambda system, tools: AnthropicSession(
            anthropic_client(), model.model, system, tools, model.effort, model.extra
        )

    if model.provider == "openai":
        from bench.llm.responses_session import ResponsesSession

        return lambda system, tools: ResponsesSession(
            openai_client(), model.model, system, tools, model.effort, model.extra
        )

    from bench.llm.chat_completions_session import ChatCompletionsSession

    base_url = os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL
    client = openai_client(base_url, "ollama")  # Ollama ignores the key
    return lambda system, tools: ChatCompletionsSession(
        client, model.model, system, tools, model.extra
    )
