"""Provider adapters, tested against fake SDK clients (no network).

The fakes return objects shaped like each SDK's responses; the tests check
that each adapter builds the right request and keeps provider-native history.
"""

from types import SimpleNamespace as NS

import anthropic
import httpx2 as httpx  # both SDKs are built on httpx2
import openai
import pytest

from bench.llm.anthropic_session import AnthropicSession
from bench.llm.base import (
    STOP_END,
    STOP_LENGTH,
    STOP_REFUSAL,
    STOP_TOOL,
    ProviderError,
    ToolResult,
    ToolSpec,
)
from bench.llm.chat_completions_session import ChatCompletionsSession, parse_arguments
from bench.llm.responses_session import ResponsesSession

TOOL = ToolSpec("run_minilang", "Run code", {"type": "object", "properties": {}})


class Recorder:
    """Fake endpoint: records each request and returns queued responses."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def create(self, **params):
        self.requests.append({**params, "messages": list(params.get("messages", []))})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


# ---------------------------------------------------------------- Anthropic
def claude_response(content, stop_reason="end_turn"):
    usage = NS(
        input_tokens=10,
        output_tokens=5,
        cache_read_input_tokens=100,
        cache_creation_input_tokens=None,
    )
    return NS(content=content, stop_reason=stop_reason, usage=usage)


def claude_client(*responses):
    endpoint = Recorder(*responses)
    return NS(messages=endpoint), endpoint


class TestAnthropicSession:
    def test_tool_call_round_trip(self):
        tool_use = NS(type="tool_use", id="tu_1", name="run_minilang", input={"code": "print(1);"})
        thinking = NS(type="thinking", thinking="", signature="sig")
        client, endpoint = claude_client(
            claude_response([thinking, tool_use], "tool_use"),
            claude_response([NS(type="text", text="done")]),
        )
        session = AnthropicSession(client, "claude-x", "SYSTEM", [TOOL], effort="medium")

        turn = session.send_user("task")
        assert turn.stop == STOP_TOOL
        assert turn.tool_calls[0].arguments == {"code": "print(1);"}
        assert turn.usage.cache_read_tokens == 100
        assert turn.usage.cache_write_tokens == 0

        final = session.send_tool_results([ToolResult("tu_1", "ok", is_error=False)])
        assert (final.text, final.stop) == ("done", STOP_END)

        first, second = endpoint.requests
        assert first["system"] == "SYSTEM"
        assert first["output_config"] == {"effort": "medium"}
        assert first["cache_control"] == {"type": "ephemeral"}
        assert first["tools"][0]["strict"] is True
        assert first["tools"][0]["input_schema"] == TOOL.parameters
        # Thinking blocks are sent back unchanged, then one tool_result message.
        assert second["messages"][1] == {"role": "assistant", "content": [thinking, tool_use]}
        assert second["messages"][2]["content"][0] == {
            "type": "tool_result",
            "tool_use_id": "tu_1",
            "content": "ok",
            "is_error": False,
        }

    @pytest.mark.parametrize(
        ("reason", "stop"), [("max_tokens", STOP_LENGTH), ("refusal", STOP_REFUSAL)]
    )
    def test_stop_reasons(self, reason, stop):
        client, _ = claude_client(claude_response([], reason))
        assert AnthropicSession(client, "m", "s", []).send_user("x").stop == stop

    def test_no_tools_or_effort_omits_those_params(self):
        client, endpoint = claude_client(claude_response([]))
        AnthropicSession(client, "m", "s", []).send_user("x")
        assert "tools" not in endpoint.requests[0]
        assert "output_config" not in endpoint.requests[0]

    def test_api_errors_become_provider_errors(self):
        request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        error = anthropic.APIConnectionError(request=request)
        client, _ = claude_client(error)
        with pytest.raises(ProviderError, match="connection error"):
            AnthropicSession(client, "m", "s", []).send_user("x")


# ---------------------------------------------------------------- Responses API
def oa_response(output, output_text="", status="completed", reason=None):
    usage = NS(input_tokens=50, output_tokens=7, input_tokens_details=NS(cached_tokens=40))
    return NS(
        output=output,
        output_text=output_text,
        status=status,
        incomplete_details=NS(reason=reason) if reason else None,
        usage=usage,
    )


class TestResponsesSession:
    def test_tool_call_round_trip(self):
        call = NS(
            type="function_call", call_id="call_1", name="run_minilang", arguments='{"code": "x"}'
        )
        reasoning = NS(type="reasoning")
        endpoint = Recorder(
            oa_response([reasoning, call]),
            oa_response([NS(type="message", content=[NS(type="output_text")])], "done"),
        )
        session = ResponsesSession(
            NS(responses=endpoint), "gpt-x", "SYSTEM", [TOOL], effort="medium"
        )

        turn = session.send_user("task")
        assert turn.stop == STOP_TOOL
        assert turn.tool_calls[0].id == "call_1"
        assert turn.usage.input_tokens == 10  # 50 prompt tokens - 40 cached
        assert turn.usage.cache_read_tokens == 40

        final = session.send_tool_results([ToolResult("call_1", "ok")])
        assert (final.text, final.stop) == ("done", STOP_END)

        first = endpoint.requests[0]
        assert first["instructions"] == "SYSTEM"
        assert first["reasoning"] == {"effort": "medium"}
        assert first["tools"][0] == {
            "type": "function",
            "name": "run_minilang",
            "description": "Run code",
            "parameters": TOOL.parameters,
            "strict": True,
        }
        items = endpoint.requests[1]["input"]
        assert items[1:3] == [reasoning, call]  # output items fed back as input
        assert items[3] == {"type": "function_call_output", "call_id": "call_1", "output": "ok"}

    def test_incomplete_response_is_a_length_stop(self):
        endpoint = Recorder(oa_response([], status="incomplete", reason="max_output_tokens"))
        assert (
            ResponsesSession(NS(responses=endpoint), "m", "s", []).send_user("x").stop
            == STOP_LENGTH
        )

    def test_refusal_content_is_detected(self):
        message = NS(type="message", content=[NS(type="refusal")])
        endpoint = Recorder(oa_response([message]))
        assert (
            ResponsesSession(NS(responses=endpoint), "m", "s", []).send_user("x").stop
            == STOP_REFUSAL
        )

    def test_api_errors_become_provider_errors(self):
        request = httpx.Request("POST", "https://api.openai.com/v1/responses")
        endpoint = Recorder(openai.APIConnectionError(request=request))
        with pytest.raises(ProviderError):
            ResponsesSession(NS(responses=endpoint), "m", "s", []).send_user("x")


# ---------------------------------------------------------------- Chat Completions (Ollama)
def chat_response(content="", tool_calls=None, finish="stop", cached=None):
    details = NS(cached_tokens=cached) if cached is not None else None
    usage = NS(prompt_tokens=30, completion_tokens=4, prompt_tokens_details=details)
    message = NS(content=content, tool_calls=tool_calls, refusal=None)
    return NS(choices=[NS(message=message, finish_reason=finish)], usage=usage)


class TestChatCompletionsSession:
    def test_tool_call_round_trip(self):
        call = NS(id="c1", function=NS(name="run_minilang", arguments='{"code": "y"}'))
        endpoint = Recorder(
            chat_response(tool_calls=[call], finish="tool_calls"), chat_response("ok")
        )
        session = ChatCompletionsSession(NS(chat=NS(completions=endpoint)), "qwen", "SYS", [TOOL])

        turn = session.send_user("task")
        assert turn.stop == STOP_TOOL
        assert turn.tool_calls[0].arguments == {"code": "y"}
        assert turn.usage.input_tokens == 30

        session.send_tool_results([ToolResult("c1", "output")])
        messages = endpoint.requests[1]["messages"]
        assert messages[0] == {"role": "system", "content": "SYS"}
        assert messages[2]["tool_calls"][0]["id"] == "c1"
        assert messages[3] == {"role": "tool", "tool_call_id": "c1", "content": "output"}

    def test_cached_tokens_are_split_out(self):
        endpoint = Recorder(chat_response("hi", cached=20))
        turn = ChatCompletionsSession(NS(chat=NS(completions=endpoint)), "m", "s", []).send_user(
            "x"
        )
        assert (turn.usage.input_tokens, turn.usage.cache_read_tokens) == (10, 20)

    @pytest.mark.parametrize(
        ("raw", "parsed"),
        [('{"code": "x"}', {"code": "x"}), ("not json", {}), ("[1, 2]", {}), (None, {})],
    )
    def test_parse_arguments_tolerates_bad_json(self, raw, parsed):
        assert parse_arguments(raw) == parsed
