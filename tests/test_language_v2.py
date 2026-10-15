"""MiniLang v2 language features, end to end (source -> output)."""

import pytest

from minilang.errors import MiniLangRuntimeError, ParserError, SemanticError


class TestArrays:
    def test_literal_index_and_len(self, run):
        assert run("let xs = [10, 20, 30]; print(xs[1]); print(len(xs));") == ["20", "3"]

    def test_empty_array_and_push_pop(self, run):
        src = "let xs = []; push(xs, 1); push(xs, 2); print(pop(xs)); print(len(xs));"
        assert run(src) == ["2", "1"]

    def test_index_assignment_and_compound(self, run):
        src = "let xs = [1, 2, 3]; xs[0] = 9; xs[2] += 10; xs[1]++; print(xs);"
        assert run(src) == ["[9, 3, 13]"]

    def test_nested_arrays(self, run):
        src = "let grid = [[1, 2], [3, 4]]; grid[1][0] = 7; print(grid[1][0] + grid[0][1]);"
        assert run(src) == ["9"]

    def test_arrays_are_shared_references(self, run):
        src = "let a = [1]; let b = a; push(b, 2); print(len(a));"
        assert run(src) == ["2"]

    def test_functions_can_mutate_array_arguments(self, run):
        src = (
            "fn fill(xs, n) { for (let i = 0; i < n; i++) { push(xs, i); } }"
            " let v = []; fill(v, 3); print(v);"
        )
        assert run(src) == ["[0, 1, 2]"]

    def test_const_array_contents_can_change(self, run):
        assert run("const xs = [1]; push(xs, 2); print(xs);") == ["[1, 2]"]

    def test_printing_quotes_strings_inside_arrays(self, run):
        assert run('print(["a", 1, true, null]);') == ['["a", 1, true, null]']

    def test_array_equality_compares_contents(self, run):
        assert run("print([1, 2] == [1, 2]); print([1] == [2]);") == ["true", "false"]

    @pytest.mark.parametrize(
        ("src", "message"),
        [
            ("let xs = [1]; print(xs[1]);", "index 1 out of range"),
            ("let xs = [1]; print(xs[-1]);", "index -1 out of range"),
            ("let xs = []; print(pop(xs));", "pop from an empty array"),
            ('fn at(xs, k) { return xs[k]; } print(at([1], "0"));', "index must be an int"),
        ],
    )
    def test_runtime_errors(self, run, src, message):
        with pytest.raises(MiniLangRuntimeError, match=message):
            run(src)


class TestStrings:
    def test_index_and_len(self, run):
        assert run('let s = "hello"; print(s[1]); print(len(s));') == ["e", "5"]

    def test_iterate_characters(self, run):
        src = (
            'let s = "abc"; let r = "";'
            " for (let i = 0; i < len(s); i++) { r = s[i] + r; } print(r);"
        )
        assert run(src) == ["cba"]

    def test_string_index_is_checked_statically(self, run):
        with pytest.raises(SemanticError, match="index must be an int, got string"):
            run('let xs = [1]; let k = "0"; print(xs[k]);')

    def test_strings_are_immutable(self, run):
        with pytest.raises(SemanticError, match="strings are immutable"):
            run('let s = "abc"; s[0] = "x";')


class TestConversions:
    @pytest.mark.parametrize(
        ("expr", "out"),
        [
            ("str(42)", "42"),
            ("str(2.5)", "2.5"),
            ("str(true)", "true"),
            ('str([1, "a"])', '[1, "a"]'),
            ("int(7 / 2)", "3"),
            ("int(-7 / 2)", "-3"),  # truncates toward zero
            ('int("42")', "42"),
            ("int(5)", "5"),
        ],
    )
    def test_conversions(self, run, expr, out):
        assert run(f"print({expr});") == [out]

    def test_string_building_with_str(self, run):
        assert run('let n = 5050; print("Sum = " + str(n));') == ["Sum = 5050"]

    def test_int_of_bad_string_is_a_runtime_error(self, run):
        with pytest.raises(MiniLangRuntimeError, match="cannot convert"):
            run('print(int("12a"));')

    def test_integer_division_keeps_variable_an_int(self, run):
        assert run("let n = 98; n = int(n / 10); print(n);") == ["9"]


class TestBuiltinChecks:
    @pytest.mark.parametrize(
        ("src", "message"),
        [
            ("print(len(5));", "len\\(\\) expects an array or string"),
            ("print(len());", "len\\(\\) expects 1 argument"),
            ("push(5, 1);", "push\\(\\) expects an array"),
            ("let len = 3;", "'len' is a built-in function"),
            ("fn str(x) { return x; }", "'str' is a built-in function"),
        ],
    )
    def test_static_errors(self, run, src, message):
        with pytest.raises(SemanticError, match=message):
            run(src)

    def test_unknown_values_are_checked_at_runtime(self, run):
        with pytest.raises(MiniLangRuntimeError, match="len\\(\\) expects an array or string"):
            run("fn f(x) { return len(x); } print(f(5));")


class TestBreakContinue:
    def test_break_leaves_the_loop(self, run):
        src = "let n = 1; while (true) { if (n * n > 2000) { break; } n++; } print(n);"
        assert run(src) == ["45"]

    def test_continue_skips_to_next_iteration_and_runs_update(self, run):
        src = "for (let i = 0; i < 6; i++) { if (i % 2 == 0) { continue; } print(i); }"
        assert run(src) == ["1", "3", "5"]

    def test_break_only_leaves_the_innermost_loop(self, run):
        src = """
        for (let i = 0; i < 3; i++) {
            for (let j = 0; j < 3; j++) { if (j == 1) { break; } print(i * 10 + j); }
        }
        """
        assert run(src) == ["0", "10", "20"]

    @pytest.mark.parametrize("stmt", ["break;", "continue;"])
    def test_outside_a_loop_is_an_error(self, run, stmt):
        with pytest.raises(SemanticError, match="outside a loop"):
            run(stmt)

    def test_loop_does_not_leak_into_function_bodies(self, run):
        with pytest.raises(SemanticError, match="outside a loop"):
            run("while (true) { fn f() { break; } }")


class TestShortCircuit:
    def test_and_skips_right_side(self, run):
        src = (
            "fn ratio(a, b) { return b != 0 && a / b > 2; }"
            " print(ratio(5, 0)); print(ratio(10, 2));"
        )
        assert run(src) == ["false", "true"]

    def test_or_skips_right_side(self, run):
        src = "let xs = []; print(len(xs) == 0 || xs[0] > 1);"
        assert run(src) == ["true"]


class TestHoisting:
    def test_mutual_recursion(self, run):
        src = """
        fn isEven(n) { if (n == 0) { return true; } return isOdd(n - 1); }
        fn isOdd(n) { if (n == 0) { return false; } return isEven(n - 1); }
        print(isEven(10));
        """
        assert run(src) == ["true"]

    def test_call_before_declaration(self, run):
        assert run("print(twice(4)); fn twice(x) { return x * 2; }") == ["8"]

    def test_hoisting_is_per_block(self, run):
        with pytest.raises(SemanticError, match="'inner' is not a declared function"):
            run("{ fn inner() { return 1; } } print(inner());")


class TestMultipleErrors:
    def test_semantic_errors_are_all_reported(self, run):
        with pytest.raises(SemanticError) as info:
            run("print(a);\nprint(b);\nlet c = 1;\nprint(d);")
        error = info.value
        assert error.message.endswith("'a' used before declaration")
        assert [e.line for e in error.additional] == [2, 4]

    def test_failed_declaration_does_not_cascade(self, run):
        with pytest.raises(SemanticError) as info:
            run("let x = missing;\nprint(x);")
        assert info.value.additional == []

    def test_syntax_errors_recover_at_statement_boundaries(self, run):
        with pytest.raises(ParserError) as info:
            run("let a = ;\nprint(1);\nlet b = 2 +;\nprint(2);")
        assert info.value.line == 1
        assert [e.line for e in info.value.additional] == [3]


class TestRecoveryQuality:
    """Recovery must not invent follow-on errors from leftovers of a broken statement."""

    def test_error_in_for_header_reports_once(self, run):
        src = "let xs = [1];\nfor (let i = 0; i < xs.length; i++) {\n  print(i);\n}\nprint(1);"
        with pytest.raises(ParserError) as info:
            run(src)
        assert info.value.additional == []

    def test_error_in_if_with_else_reports_once(self, run):
        src = "if (1 +) { print(1); } else { print(2); }\nprint(3);"
        with pytest.raises(ParserError) as info:
            run(src)
        assert info.value.additional == []

    def test_errors_inside_a_body_are_still_found_individually(self, run):
        src = "fn f() {\n  let a = ;\n  let b = 2 +;\n}"
        with pytest.raises(ParserError) as info:
            run(src)
        assert [info.value.line, *[e.line for e in info.value.additional]] == [2, 3]

    def test_stray_closing_brace_does_not_hang(self, run):
        with pytest.raises(ParserError):
            run("}\nprint(1);")
