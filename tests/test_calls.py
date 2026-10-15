"""Calls on any expression: functions are first-class values.

A call is a postfix operator, like indexing, so whatever an expression
produces can be called: f(x) on a parameter, makeAdder(5)(10), fs[0]().
"""

import pytest

from minilang.errors import MiniLangRuntimeError, SemanticError
from tests.test_codegen import tac
from tests.test_parser import expr, sexpr


class TestParsing:
    def test_chained_call(self):
        assert sexpr(expr("f(1)(2)")) == "(call (call f 1) 2)"

    def test_call_on_index(self):
        assert sexpr(expr("fs[0](3)")) == "(call (index fs 0) 3)"

    def test_index_on_call_result(self):
        assert sexpr(expr("f()[1]")) == "(index (call f) 1)"

    def test_call_on_parenthesized_expression(self):
        assert sexpr(expr("(f)(1)")) == "(call f 1)"


class TestRunning:
    def test_call_through_a_parameter(self, run):
        src = "fn twice(f, x) { return f(f(x)); } fn inc(n) { return n + 1; } print(twice(inc, 5));"
        assert run(src) == ["7"]

    def test_call_through_a_variable(self, run):
        assert run("fn sq(x) { return x * x; } let g = sq; print(g(4));") == ["16"]

    def test_call_a_returned_closure(self, run):
        src = "fn makeAdder(n) { fn add(x) { return x + n; } return add; } print(makeAdder(5)(10));"
        assert run(src) == ["15"]

    def test_call_from_an_array(self, run):
        src = (
            "fn inc(x) { return x + 1; } fn dbl(x) { return x * 2; }"
            " let fs = [inc, dbl];"
            " for (let i = 0; i < len(fs); i++) { print(fs[i](10)); }"
        )
        assert run(src) == ["11", "20"]

    def test_counter_closure_keeps_state(self, run):
        src = (
            "fn counter() { let n = 0; fn next() { n++; return n; } return next; }"
            " let c = counter(); c(); c(); print(c());"
        )
        assert run(src) == ["3"]


class TestErrors:
    @pytest.mark.parametrize(
        ("src", "message"),
        [
            ("let x = 5; x(1);", "cannot call a value of type int"),
            ('"abc"(1);', "cannot call a value of type string"),
            ("fn f() { return 1; } f()(2)(3);", None),  # runtime: 1 is not callable
        ],
    )
    def test_calling_a_non_function(self, run, src, message):
        if message is None:
            with pytest.raises(MiniLangRuntimeError, match="cannot call a value of type int"):
                run(src)
        else:
            with pytest.raises(SemanticError, match=message):
                run(src)

    def test_wrong_arity_through_a_variable_is_a_runtime_error(self, run):
        src = "fn sq(x) { return x * x; } let g = sq; print(g(1, 2));"
        with pytest.raises(MiniLangRuntimeError, match="expects 1 argument"):
            run(src)

    def test_unknown_function_name_still_suggests_a_fix(self, run):
        with pytest.raises(SemanticError, match="'sqare' is not a declared function") as caught:
            run("fn square(x) { return x * x; } print(sqare(2));")
        assert caught.value.hint == "did you mean 'square'?"


class TestCodegen:
    def test_named_call_is_unchanged(self):
        assert tac("fn f(x) { return x; } f(1);")[-2:] == ["param 1", "t1 = call f, 1"]

    def test_call_on_an_expression_calls_a_temp(self):
        assert tac("fs[0](7);") == ["t1 = fs[0]", "param 7", "t2 = call t1, 1"]
