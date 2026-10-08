"""Interpreter and value-semantics unit tests."""

import pytest

from minilang.errors import MiniLangRuntimeError
from minilang.runtime import Environment
from minilang.values import apply_binary, format_value, literal_value, type_name


class TestPrograms:
    def test_closures_see_later_updates_to_globals(self, run):
        src = "let n = 1; fn get() { return n; } n = 5; print(get());"
        assert run(src) == ["5"]

    def test_function_can_modify_outer_variable(self, run):
        src = "let count = 0; fn bump() { count += 1; } bump(); bump(); print(count);"
        assert run(src) == ["2"]

    def test_parameters_are_local(self, run):
        src = "let x = 1; fn f(x) { x = 99; return x; } print(f(5)); print(x);"
        assert run(src) == ["99", "1"]

    def test_loop_variable_is_scoped_to_the_loop(self, run):
        src = "for (let i = 0; i < 2; i++) { print(i); } let i = 10; print(i);"
        assert run(src) == ["0", "1", "10"]

    def test_function_without_return_gives_null(self, run):
        assert run("fn f() { } print(f());") == ["null"]

    def test_postfix_returns_old_value_prefix_returns_new(self, run):
        assert run("let i = 5; print(i++); print(i); print(++i);") == ["5", "6", "7"]

    def test_integer_division_produces_float(self, run):
        assert run("print(7 / 2); print(4 / 2);") == ["3.5", "2.0"]

    def test_modulo_and_negative_numbers(self, run):
        assert run("print(7 % 3); print(-7 + 2);") == ["1", "-5"]

    def test_fizzbuzz(self, run):
        src = """
        for (let i = 1; i <= 15; i++) {
            if (i % 15 == 0) { print("FizzBuzz"); }
            else if (i % 3 == 0) { print("Fizz"); }
            else if (i % 5 == 0) { print("Buzz"); }
            else { print(i); }
        }
        """
        out = run(src)
        assert out[2] == "Fizz" and out[4] == "Buzz" and out[14] == "FizzBuzz"


class TestEnvironment:
    def test_redefinition_in_same_scope_fails(self):
        env = Environment()
        env.define("a", 1)
        with pytest.raises(MiniLangRuntimeError, match="already defined"):
            env.define("a", 2)

    def test_undefined_lookup_and_assignment_fail(self):
        with pytest.raises(MiniLangRuntimeError, match="undefined variable"):
            Environment().resolve("nope")
        with pytest.raises(MiniLangRuntimeError, match="undefined variable"):
            Environment().assign("nope", 1)

    def test_const_binding_cannot_be_assigned(self):
        env = Environment()
        env.define("c", 1, mutable=False)
        with pytest.raises(MiniLangRuntimeError, match="cannot be reassigned"):
            env.assign("c", 2)

    def test_child_scope_reads_and_writes_parent(self):
        parent = Environment()
        parent.define("a", 1)
        Environment(parent).assign("a", 2)
        assert parent.resolve("a").value == 2


class TestValues:
    @pytest.mark.parametrize(
        ("value", "name"),
        [(True, "bool"), (1, "int"), (1.0, "float"), ("s", "string"), (None, "null")],
    )
    def test_type_name(self, value, name):
        assert type_name(value) == name

    def test_bool_is_not_equal_to_int(self):
        # Python says True == 1; MiniLang must not.
        assert apply_binary("==", True, 1) is False
        assert apply_binary("!=", True, 1) is True

    def test_strict_equality_distinguishes_int_and_float(self):
        assert apply_binary("==", 1, 1.0) is True
        assert apply_binary("===", 1, 1.0) is False

    @pytest.mark.parametrize(
        ("op", "left", "right"),
        [("+", True, 1), ("<", "a", "b"), ("*", "a", 2), ("-", None, 1)],
    )
    def test_operators_reject_wrong_runtime_types(self, op, left, right):
        with pytest.raises(MiniLangRuntimeError, match="cannot apply"):
            apply_binary(op, left, right)

    def test_unknown_operator(self):
        with pytest.raises(MiniLangRuntimeError, match="unknown operator"):
            apply_binary("??", 1, 2)

    def test_logical_operators(self):
        assert apply_binary("&&", True, False) is False
        assert apply_binary("||", False, True) is True

    def test_literal_value_conversion(self):
        assert literal_value("42", "int") == 42
        assert literal_value("42", "string") == "42"
        assert literal_value("false", "bool") is False
        with pytest.raises(MiniLangRuntimeError):
            literal_value("x", None)

    def test_format_value(self):
        assert [format_value(v) for v in (True, None, 2.5, "s")] == ["true", "null", "2.5", "s"]
