"""The interpreter must stop runaway programs with a clean MiniLang error.

This matters once programs come from an LLM: an infinite loop or unbounded
recursion must not hang or crash the host process.
"""

import pytest

from minilang.errors import MiniLangRuntimeError
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.runtime import MiniRuntime, RuntimeLimits


def execute(source: str, limits: RuntimeLimits | None = None) -> list[str]:
    ast = Parser(Lexer(source).tokenize()).parse()
    return MiniRuntime(limits or RuntimeLimits()).run(ast)


def test_infinite_loop_hits_step_limit():
    with pytest.raises(MiniLangRuntimeError, match="step limit"):
        execute("while (true) { }", RuntimeLimits(max_steps=1_000))


def test_unbounded_recursion_hits_call_depth_limit():
    # Bug 7: this used to crash with Python's RecursionError.
    with pytest.raises(MiniLangRuntimeError, match="call depth"):
        execute("fn f(n) { return f(n + 1); } f(0);")


def test_runaway_printing_hits_output_limit():
    with pytest.raises(MiniLangRuntimeError, match="output limit"):
        execute("while (true) { print(1); }", RuntimeLimits(max_output_lines=50))


def test_limit_error_points_at_the_offending_code():
    with pytest.raises(MiniLangRuntimeError) as info:
        execute("let i = 0;\nwhile (true) { i++; }", RuntimeLimits(max_steps=100))
    assert info.value.line == 2


def test_default_limits_allow_reasonably_deep_recursion():
    src = "fn sum(n) { if (n == 0) { return 0; } return n + sum(n - 1); } print(sum(400));"
    assert execute(src) == ["80200"]


def test_default_limits_allow_reasonably_long_loops():
    src = "let t = 0; for (let i = 0; i < 20000; i++) { t += i; } print(t);"
    assert execute(src) == ["199990000"]


def test_call_depth_resets_after_returning():
    # 300 sequential calls, never more than 1 deep.
    src = (
        "fn one() { return 1; } let t = 0; for (let i = 0; i < 300; i++) { t += one(); } print(t);"
    )
    assert execute(src, RuntimeLimits(max_call_depth=5)) == ["300"]
