"""The playground API: every compiler stage as JSON-ready data for a UI."""

import json

from minilang.playground import explore


def test_successful_program_has_every_stage():
    result = explore("let x = 1 + 2;\nprint(x);")
    assert result["ok"] is True
    assert result["failed_stage"] is None
    assert result["tokens"][0] == {"type": "KW", "value": "let", "line": 1, "col": 1}
    assert result["ast"]["kind"] == "Program"
    assert result["ast"]["children"][0]["kind"] == "VarDecl"
    assert result["tac"] == ["t1 = 1 + 2", "x = t1", "print x"]
    assert result["asm"]
    assert result["output"] == ["3"]
    assert result["errors"] == []
    assert set(result["timings_ms"]) == {"lex", "parse", "check", "codegen", "run"}


def test_result_is_json_serializable():
    json.dumps(explore("fn f(x) { return x; } print(f([1, 'a']));"))


def test_ast_nodes_carry_values_and_positions():
    literal = explore("print(42);")["ast"]["children"][0]["children"][0]
    assert literal == {
        "kind": "Literal",
        "value": "42",
        "type": "int",
        "line": 1,
        "col": 7,
        "children": [],
    }


def test_syntax_error_keeps_the_tokens():
    result = explore("let x = ;")
    assert result["ok"] is False
    assert result["failed_stage"] == "syntax"
    assert result["tokens"] is not None
    assert result["ast"] is None and result["tac"] is None
    assert result["errors"][0]["line"] == 1
    assert "error[syntax]" in result["diagnostic"]


def test_every_error_is_listed_with_hints():
    result = explore("let total = 1;\nprint(totl);\nprint(xs.length);")
    assert result["failed_stage"] == "syntax"
    messages = [e["message"] for e in result["errors"]]
    assert any("expected" in m for m in messages)


def test_semantic_error_keeps_the_ast():
    result = explore("let total = 1; print(totl);")
    assert result["failed_stage"] == "semantic"
    assert result["ast"] is not None
    assert result["errors"][0]["hint"] == "did you mean 'total'?"


def test_runtime_error_keeps_compiled_code_and_partial_output():
    result = explore("print(1);\nprint(1 / 0);")
    assert result["failed_stage"] == "runtime"
    assert result["tac"] is not None
    assert result["output"] == ["1"]
    assert "division by zero" in result["errors"][0]["message"]


def test_lexer_error_has_no_tokens():
    result = explore('let s = "unterminated;')
    assert result["failed_stage"] == "lexer"
    assert result["tokens"] is None


def test_runaway_program_is_stopped():
    result = explore("while (true) { }")
    assert result["failed_stage"] == "runtime"
    assert "step limit exceeded (200000 statements)" in result["errors"][0]["message"]
