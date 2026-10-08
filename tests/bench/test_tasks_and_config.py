"""Benchmark health: tasks are solvable and configuration is valid."""

import pytest

from bench.config import Price, load_models, parse_model
from bench.llm.base import Usage
from bench.tasks import load_tasks, parse_task
from minilang.pipeline import run_source

TASKS = load_tasks()


@pytest.mark.parametrize("task", TASKS, ids=[t.id for t in TASKS])
def test_reference_solution_produces_expected_output(task):
    # An unsolvable task would silently cap every model's score.
    result = run_source(task.reference)
    assert result.ok, result.diagnostic
    assert tuple(result.output) == task.expected


def test_task_suite_shape():
    assert len(TASKS) == 25
    assert {t.tier for t in TASKS} == {1, 2, 3}


def test_user_message_shows_expected_output_but_not_reference():
    task = next(t for t in TASKS if t.id == "gcd")
    message = task.user_message()
    assert "6\n1\n25" in message
    assert "while (b != 0)" not in message


@pytest.mark.parametrize(
    ("raw", "error"),
    [
        ({"id": "x"}, "missing"),
        ({"id": "x", "tier": 9, "prompt": "p", "expected": "1", "reference": "r"}, "tier"),
    ],
)
def test_invalid_tasks_are_rejected(raw, error):
    with pytest.raises(ValueError, match=error):
        parse_task(raw)


def test_models_file_is_valid():
    models = load_models()
    assert {m.provider for m in models} == {"anthropic", "openai", "ollama"}
    assert all(m.price.input >= 0 for m in models)


def test_unknown_provider_is_rejected():
    raw = {
        "id": "x",
        "provider": "acme",
        "model": "m",
        "tier": "t",
        "price": {"input": 1, "output": 1},
    }
    with pytest.raises(ValueError, match="unknown provider"):
        parse_model(raw)


def test_availability_depends_on_api_key(monkeypatch):
    raw = {
        "id": "x",
        "provider": "anthropic",
        "model": "m",
        "tier": "t",
        "price": {"input": 1, "output": 1},
    }
    model = parse_model(raw)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    assert not model.is_available()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    assert model.is_available()
    ollama = parse_model({**raw, "provider": "ollama"})
    assert ollama.is_available()


def test_cost_includes_cache_pricing():
    price = Price(input=2.0, output=10.0)
    usage = Usage(input_tokens=1_000_000, output_tokens=100_000, cache_read_tokens=1_000_000)
    # 2.00 input + 1.00 output + 0.20 cache reads (0.1x)
    assert price.cost(usage) == pytest.approx(3.20)


@pytest.mark.parametrize(
    ("model_id", "session_type"),
    [
        ("claude-haiku", "AnthropicSession"),
        ("gpt-luna", "ResponsesSession"),
        ("qwen-3b-local", "ChatCompletionsSession"),
    ],
)
def test_registry_builds_the_right_session(monkeypatch, model_id, session_type):
    from bench.llm.registry import session_factory

    # Clients are constructed but never called, so dummy keys are fine.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    model = next(m for m in load_models() if m.id == model_id)
    session = session_factory(model)("system", [])
    assert type(session).__name__ == session_type
