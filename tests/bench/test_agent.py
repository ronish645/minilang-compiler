"""Agent loop behavior, driven by a scripted fake model (no API calls)."""

import pytest

from bench.agent import AgentLimits, run_episode
from bench.feedback import DIAGNOSTIC, HINT, MESSAGE, ONESHOT, OPAQUE
from bench.llm.base import STOP_REFUSAL, ProviderError, Turn
from bench.tasks import Task
from tests.bench.fakes import FakeSession, factory_for, reply, run, submit

TASK = Task("three", 1, "Print 3.", ("3",), "print(3);")
SPEC = "spec text"


def episode(turns, condition=DIAGNOSTIC, limits=None):
    session = FakeSession(turns)
    result = run_episode(factory_for(session), "fake", TASK, condition, SPEC, limits=limits)
    return result, session


def test_run_then_submit_passes():
    ep, session = episode([run("print(3);"), submit("print(3);")])
    assert ep.outcome == "passed"
    assert ep.model_turns == 2
    assert [r.ok for r in ep.runs] == [True]
    assert "Output:\n3" in session.tool_results[0][0].content


def test_model_repairs_after_error():
    ep, session = episode([run("print(x);"), run("print(3);"), submit("print(3);")])
    assert ep.passed
    assert [r.ok for r in ep.runs] == [False, True]
    assert ep.runs[0].stage == "semantic"
    assert session.tool_results[0][0].is_error


def test_submitted_code_is_graded_not_last_run():
    ep, _ = episode([run("print(3);"), submit("print(4);")])
    assert ep.outcome == "wrong_output"
    assert ep.output == ["4"]


@pytest.mark.parametrize(
    ("code", "outcome"),
    [("print(;", "compile_error"), ("let z = 0; print(1 / z);", "runtime_error")],
)
def test_failing_submissions(code, outcome):
    ep, _ = episode([submit(code)])
    assert ep.outcome == outcome
    assert ep.error


@pytest.mark.parametrize(
    ("condition", "expected_fragment", "absent_fragment"),
    [
        (OPAQUE, "the program failed", "used before declaration"),
        (MESSAGE, "variable 'x' used before declaration", "-->"),
        (DIAGNOSTIC, "--> program.ml:1:7", "help"),
    ],
)
def test_feedback_depends_on_condition(condition, expected_fragment, absent_fragment):
    _, session = episode([run("print(x);"), submit("print(3);")], condition=condition)
    feedback = session.tool_results[0][0].content
    assert expected_fragment in feedback
    if absent_fragment:
        assert absent_fragment not in feedback


def test_stopping_without_submit_grades_code_block_in_reply():
    ep, _ = episode([reply("Here you go:\n```minilang\nprint(3);\n```")])
    assert ep.passed


def test_stopping_without_submit_or_code_falls_back_to_last_run():
    ep, _ = episode([run("print(3);"), reply("Done!")])
    assert ep.passed


def test_no_code_at_all():
    ep, _ = episode([reply("I cannot do this.")])
    assert ep.outcome == "no_code"


def test_run_budget_is_enforced():
    limits = AgentLimits(max_runs=1, max_model_turns=8)
    ep, session = episode([run("print(1);"), run("print(2);"), submit("print(3);")], limits=limits)
    assert len(ep.runs) == 1
    assert "Run limit reached" in session.tool_results[1][0].content
    assert ep.passed


def test_turn_limit_ends_episode():
    limits = AgentLimits(max_runs=10, max_model_turns=2)
    ep, _ = episode([run("print(x);"), run("print(y);"), run("print(z);")], limits=limits)
    assert ep.outcome == "turn_limit"
    assert ep.model_turns == 2


def test_unknown_tool_and_bad_arguments_are_reported_to_the_model():
    from bench.llm.base import STOP_TOOL, ToolCall

    turn = Turn(
        "",
        [ToolCall("a", "delete_files", {"code": "x"}), ToolCall("b", "run_minilang", {})],
        STOP_TOOL,
    )
    _, session = episode([turn, submit("print(3);")])
    contents = [r.content for r in session.tool_results[0]]
    assert "unknown tool" in contents[0]
    assert "must be a string" in contents[1]


def test_refusal():
    ep, _ = episode([Turn("", [], STOP_REFUSAL)])
    assert ep.outcome == "refusal"


def test_oneshot_sends_no_tools_and_extracts_code():
    ep, session = episode([reply("```\nprint(3);\n```")], condition=ONESHOT)
    assert ep.passed
    assert session.tools == []
    assert "cannot run code" in session.system


def test_tool_conditions_offer_both_tools_and_include_spec():
    _, session = episode([submit("print(3);")])
    assert [t.name for t in session.tools] == ["run_minilang", "submit_solution"]
    assert SPEC in session.system
    assert "print exactly this output" in session.user_messages[0]


def test_provider_error_is_recorded_not_raised():
    def failing_factory(system, tools):
        raise ProviderError("anthropic 529: overloaded")

    ep = run_episode(failing_factory, "fake", TASK, DIAGNOSTIC, SPEC)
    assert ep.outcome == "api_error"
    assert "overloaded" in ep.error


def test_usage_accumulates_across_turns():
    ep, _ = episode([run("print(3);"), submit("print(3);")])
    assert (ep.usage.input_tokens, ep.usage.output_tokens) == (20, 10)


def test_episode_round_trips_through_dict():
    from bench.agent import Episode

    ep, _ = episode([run("print(x);"), submit("print(3);")])
    assert Episode.from_dict(ep.to_dict()) == ep


def test_hint_condition_shows_every_error_with_help():
    code = "let total = 1;\nprint(totl);\nprint(zz);"
    _, session = episode([run(code), submit("print(3);")], condition=HINT)
    feedback = session.tool_results[0][0].content
    assert "did you mean 'total'?" in feedback
    assert "2 errors found." in feedback


def test_diagnostic_condition_shows_only_the_first_error_without_help():
    code = "let total = 1;\nprint(totl);\nprint(zz);"
    _, session = episode([run(code), submit("print(3);")], condition=DIAGNOSTIC)
    feedback = session.tool_results[0][0].content
    assert feedback.count("error[") == 1
    assert "help" not in feedback


def test_runtime_error_feedback_includes_partial_output():
    code = "print(1);\nlet z = 0;\nprint(1 / z);"
    _, session = episode([run(code), submit("print(3);")], condition=HINT)
    assert "Output printed before the error:\n1" in session.tool_results[0][0].content
