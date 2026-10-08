"""Every error must name its stage and point at the right line/column."""

import pytest

from minilang.diagnostics import format_diagnostic
from minilang.errors import (
    LexerError,
    MiniLangError,
    MiniLangRuntimeError,
    ParserError,
    SemanticError,
)
from minilang.pipeline import compile_source


def error_for(source: str) -> MiniLangError:
    with pytest.raises(MiniLangError) as info:
        compile_source(source)
    return info.value


@pytest.mark.parametrize(
    ("source", "error_type", "line", "col", "message"),
    [
        ("let a = 1 @ 2;", LexerError, 1, 11, "unexpected character '@'"),
        ('print("open);', LexerError, 1, 7, "unterminated string"),
        ("let a = 1;\n/* never closed", LexerError, 2, 1, "unterminated block comment"),
        ("let a = 1\nprint(a);", ParserError, 1, 10, "expected ';' but found 'print'"),
        ("print(1 + );", ParserError, 1, 11, "expected an expression but found ')'"),
        ("fn f() {\n  print(1);\n", ParserError, 1, 8, "unclosed block"),
        ("let 5 = 1;", ParserError, 1, 5, "expected an identifier"),
        ("print(y);", SemanticError, 1, 7, "'y' used before declaration"),
        ("const c = 1;\nc = 2;", SemanticError, 2, 3, "cannot be reassigned"),
        ("let a = 1;\nlet a = 2;", SemanticError, 2, 1, "already declared"),
        ("fn f(a) { return a; }\nf(1, 2);", SemanticError, 2, 1, "expects 1 argument(s), got 2"),
        ("return 1;", SemanticError, 1, 1, "return statement outside function"),
        ("if (1) { print(1); }", SemanticError, 1, 5, "condition must be boolean, got int"),
        ("let z = 0;\nprint(1 / z);", MiniLangRuntimeError, 2, 9, "division by zero"),
    ],
)
def test_error_stage_position_and_message(source, error_type, line, col, message):
    # Act
    error = error_for(source)

    # Assert
    assert type(error) is error_type
    assert (error.line, error.col) == (line, col)
    assert message in error.message


def test_missing_semicolon_on_same_line_points_at_next_token():
    error = error_for("let a = 1 print(a);")
    assert (error.line, error.col) == (1, 11)


def test_str_includes_stage_and_position():
    assert str(error_for("print(y);")) == (
        "Semantic error at line 1, col 7: variable 'y' used before declaration"
    )


def test_to_dict_is_json_friendly():
    assert error_for("print(y);").to_dict() == {
        "stage": "semantic",
        "message": "variable 'y' used before declaration",
        "line": 1,
        "col": 7,
    }


def test_runtime_error_keeps_output_printed_before_the_failure():
    error = error_for("print(1);\nprint(2);\nlet z = 0;\nprint(1 / z);")
    assert isinstance(error, MiniLangRuntimeError)
    assert error.partial_output == ["1", "2"]


class TestFormatDiagnostic:
    def test_renders_source_line_and_caret(self):
        source = "let x = 1;\nprint(y);"
        rendered = format_diagnostic(error_for(source), source, "prog.ml")
        assert rendered == (
            "error[semantic]: variable 'y' used before declaration\n"
            " --> prog.ml:2:7\n"
            "  |\n"
            "2 | print(y);\n"
            "  |       ^"
        )

    def test_caret_follows_tabs(self):
        source = "\tprint(y);"
        rendered = format_diagnostic(error_for(source), source)
        assert rendered.splitlines()[-1] == "  | \t      ^"

    def test_error_without_position_renders_header_only(self):
        assert format_diagnostic(SemanticError("boom"), "") == "error[semantic]: boom"

    def test_position_past_end_of_source_omits_snippet(self):
        rendered = format_diagnostic(ParserError("eof", 9, 1), "one line", "f.ml")
        assert rendered == "error[syntax]: eof\n --> f.ml:9:1"
