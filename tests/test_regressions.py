"""Regression tests for bugs found in the original compiler (2026-10-08).

Each test names the bug it guards against. All of them failed before the fix.
"""

import pytest

from minilang.errors import MiniLangRuntimeError, SemanticError


class TestUnknownTypesAreGradual:
    """Bug 1-2: parameters and call results have type 'unknown', which the
    analyzer treated as incompatible with everything."""

    def test_parameter_can_be_compared_with_equality(self, run):
        src = "fn isEven(n) { return n % 2 == 0; } print(isEven(4));"
        assert run(src) == ["true"]

    def test_call_result_can_be_an_if_condition(self, run):
        src = "fn yes() { return true; } if (yes()) { print(1); }"
        assert run(src) == ["1"]

    def test_call_result_can_be_a_while_condition(self, run):
        src = """
        fn below(i, n) { return i < n; }
        let i = 0;
        while (below(i, 3)) { i++; }
        print(i);
        """
        assert run(src) == ["3"]

    def test_call_results_work_with_logical_operators(self, run):
        src = "fn t() { return true; } print(t() && !t() || t());"
        assert run(src) == ["true"]

    def test_unary_minus_on_parameter(self, run):
        assert run("fn neg(x) { return -x; } print(neg(5));") == ["-5"]


class TestLiteralTypesSurviveParsing:
    """Bug 3-4: the parser dropped the token type, so the string "42" was
    treated as the integer 42 and the string "true" as a boolean."""

    def test_numeric_looking_string_is_a_string(self, run):
        with pytest.raises(SemanticError):
            run('let s = "42"; print(s - 1);')

    def test_true_string_is_not_a_boolean(self, run):
        with pytest.raises(SemanticError, match="condition must be boolean"):
            run('let s = "true"; if (s) { print(1); }')

    def test_numeric_looking_string_prints_unchanged(self, run):
        assert run('print("007");') == ["007"]


class TestValuesPrintAsMiniLang:
    """Bug 5: Python's True/None leaked into program output."""

    @pytest.mark.parametrize(
        ("expr", "expected"),
        [("true", "true"), ("false", "false"), ("null", "null"), ("1 < 2", "true")],
    )
    def test_print_uses_minilang_spelling(self, run, expr, expected):
        assert run(f"print({expr});") == [expected]

    def test_uninitialized_variable_prints_null(self, run):
        assert run("let x; print(x);") == ["null"]


class TestArithmeticFailuresAreRuntimeErrors:
    """Bug 6: dividing by zero crashed with a Python ZeroDivisionError."""

    @pytest.mark.parametrize("op", ["/", "%"])
    def test_division_by_zero(self, run, op):
        with pytest.raises(MiniLangRuntimeError, match="division by zero"):
            run(f"let z = 0; print(10 {op} z);")

    def test_runtime_type_mismatch_is_reported(self, run):
        # 'unknown' parameters pass static checks, so this is caught at runtime.
        with pytest.raises(MiniLangRuntimeError, match="cannot apply"):
            run('fn add(a, b) { return a + b; } print(add(1, "x"));')


class TestStringConcatenation:
    """Bug 8: '+' on two strings was rejected."""

    def test_string_plus_string(self, run):
        assert run('print("Fizz" + "Buzz");') == ["FizzBuzz"]

    def test_string_plus_number_is_rejected(self, run):
        with pytest.raises(SemanticError, match="'\\+'"):
            run('print("a" + 1);')

    def test_concatenated_variable_keeps_string_type(self, run):
        src = 'let s = "a"; s = s + "b"; print(s);'
        assert run(src) == ["ab"]
