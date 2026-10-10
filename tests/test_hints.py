"""Fix-it hints: habits from other languages get a specific suggestion."""

import pytest

from minilang.diagnostics import format_diagnostic
from minilang.errors import MiniLangError
from minilang.pipeline import compile_source, run_source


def error_for(source: str) -> MiniLangError:
    with pytest.raises(MiniLangError) as info:
        compile_source(source)
    return info.value


@pytest.mark.parametrize(
    ("source", "hint_fragment"),
    [
        # syntax habits
        ("let xs = [1]; print(xs.length);", "no methods or properties"),
        ('console.log("hi");', "print a value with print(x)"),
        ("let a = 1; let b = a > 0 ? 1 : 2;", "no ternary operator"),
        ("let x = 7; x %= 2;", "no %= operator"),
        ("function f() { return 1; }", "declared with fn"),
        ("var x = 1;", "declare variables with let"),
        ("for i in xs { }", "C-style loop"),
        ("if x > 1 { print(1); }", "condition needs parentheses"),
        ("fn f() return 1;", "function bodies need braces"),
        # semantic habits
        ("let total = 1; print(totl);", "did you mean 'total'?"),
        ("let x = True;", "booleans are lowercase"),
        ("let x = None;", "null"),
        ("fn add(a, b) { return a + b; } print(ad(1, 2));", "did you mean 'add'?"),
        ("let xs = [1]; print(length(xs));", "use len(x)"),
        ("let xs = []; append(xs, 1);", "use push(xs, v)"),
        ('let n = 5; print("n = " + n);', 'str(n): "Total: " + str(n)'),
        ("let n = 10; n = n / 2;", "for integer division use int(a / b)"),
        ('let s = "abc"; s[0] = "x";', "build a new string"),
    ],
)
def test_hint_for_common_mistake(source, hint_fragment):
    error = error_for(source)
    hints = [e.hint for e in (error, *error.additional) if e.hint]
    assert any(hint_fragment in h for h in hints), (error.message, hints)


def test_runtime_negative_index_hint():
    result = run_source("fn last(xs) { return xs[-1]; } print(last([1, 2]));")
    assert "no negative indexes" in result.error["hint"]


def test_no_hint_when_nothing_matches():
    assert error_for("let a = 1; let a = 2;").hint is None


def test_hint_is_rendered_as_help_line():
    source = "let total = 1;\nprint(totl);"
    rendered = format_diagnostic(error_for(source), source, "p.ml")
    assert rendered.splitlines()[-1] == "  = help: did you mean 'total'?"


def test_hints_can_be_left_out():
    source = "let total = 1;\nprint(totl);"
    rendered = format_diagnostic(error_for(source), source, include_hints=False)
    assert "help" not in rendered


def test_multiple_errors_render_with_count_and_can_be_limited():
    source = "print(a);\nprint(b);"
    error = error_for(source)
    full = format_diagnostic(error, source)
    assert full.count("error[semantic]") == 2
    assert full.endswith("2 errors found.")
    first_only = format_diagnostic(error, source, include_additional=False)
    assert first_only.count("error[semantic]") == 1


def test_to_dict_includes_hint_and_additional_errors():
    data = error_for("print(totl);\nlet total = 1;\nprint(zz);").to_dict()
    assert data["message"] == "variable 'totl' used before declaration"
    assert [e["line"] for e in data["additional"]] == [3]


def test_error_limit_stops_collecting():
    source = "\n".join(f"print(v{i});" for i in range(30))
    error = error_for(source)
    assert 1 + len(error.additional) == 10
