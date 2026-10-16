"""Resource limits against hostile programs: memory, output size, time and nesting.

Every program here is tiny but would exhaust memory, CPU or the Python stack
without a limit. Each must end with a clean MiniLang error, never a crash.
"""

import sys
import threading

import pytest

from minilang.errors import MiniLangError, MiniLangRuntimeError, ParserError
from minilang.pipeline import analyze_source
from minilang.playground import PLAYGROUND_LIMITS, explore
from minilang.runtime import MiniRuntime, RuntimeLimits, python_recursion_limit
from minilang.service import check_program, compile_program, run_program

SMALL = RuntimeLimits(
    max_steps=200_000,
    max_string_length=1_000,
    max_array_length=10_000,
    max_int_bits=256,
    max_output_chars=2_000,
    # Building a 900-char string one char at a time allocates 1 + 2 + ... + 900 ≈ 405,000.
    max_alloc_units=1_000_000,
)


def run_with(source: str, limits: RuntimeLimits) -> list[str]:
    _, _, ast = analyze_source(source)
    return MiniRuntime(limits).run(ast)


def fails_with(source: str, message: str, limits: RuntimeLimits = SMALL) -> MiniLangRuntimeError:
    with pytest.raises(MiniLangRuntimeError, match=message) as caught:
        run_with(source, limits)
    return caught.value


class TestMemory:
    def test_string_doubling_is_stopped_before_allocating(self):
        src = 'let s = "aaaaaaaaaaaaaaaa"; for (let i = 0; i < 40; i++) { s = s + s; }'
        fails_with(src, "string too long")

    def test_compound_assignment_is_checked_too(self):
        src = 'let s = "ab"; for (let i = 0; i < 40; i++) { s += s; }'
        fails_with(src, "string too long")

    def test_many_medium_strings_hit_the_allocation_budget(self):
        src = (
            'let s = ""; for (let i = 0; i < 900; i++) { s = s + "x"; }'
            " let keep = []; for (let i = 0; i < 1000; i++) { push(keep, s + str(i)); }"
        )
        fails_with(src, "memory limit exceeded")

    def test_integer_squaring_is_stopped(self):
        src = "let x = 3; for (let i = 0; i < 40; i++) { x = x * x; }"
        fails_with(src, "integer too large")

    def test_array_growth_is_capped(self):
        src = "let xs = []; for (let i = 0; i < 20000; i++) { push(xs, i); }"
        fails_with(src, "array too long")

    def test_slice_and_str_results_count_against_the_budget(self):
        src = (
            'let s = ""; for (let i = 0; i < 900; i++) { s = s + "y"; }'
            " for (let i = 0; i < 1000; i++) { let t = slice(s, 0, 900); }"
        )
        fails_with(src, "memory limit exceeded")

    def test_str_of_a_huge_array_is_refused_before_building_it(self):
        src = 'let s = ""; for (let i = 0; i < 500; i++) { s = s + "z"; }' + (
            " let xs = []; for (let i = 0; i < 800; i++) { push(xs, s); } let t = str(xs);"
        )
        fails_with(src, "too large to convert to text")

    def test_normal_programs_are_unaffected(self):
        src = (
            "fn fact(n) { if (n <= 1) { return 1; } return n * fact(n - 1); }"
            ' let s = ""; for (let i = 0; i < 50; i++) { s = s + str(i % 10); }'
            " print(fact(20)); print(len(s));"
        )
        assert run_with(src, SMALL) == ["2432902008176640000", "50"]


class TestNumbers:
    def test_huge_int_to_float_is_a_clean_error(self):
        # Python raises OverflowError converting a huge int to a float.
        src = "let x = 2; for (let i = 0; i < 11; i++) { x = x * x; } print(x / 3);"
        fails_with(src, "number too large", RuntimeLimits(max_int_bits=4096))

    def test_int_of_infinity_is_a_clean_error(self):
        src = "let f = 1.0; for (let i = 0; i < 400; i++) { f = f * 10.0; } print(int(f));"
        fails_with(src, "cannot convert", RuntimeLimits())

    def test_default_int_limit_keeps_printing_possible(self):
        # Python can't print ints over ~4300 digits; the default limit stays below that.
        src = "let x = 1; for (let i = 0; i < 20000; i++) { x = x * 2; } print(x);"
        fails_with(src, "integer too large", RuntimeLimits())


class TestOutput:
    def test_total_printed_characters_are_capped(self):
        src = 'let s = ""; for (let i = 0; i < 500; i++) { s = s + "o"; }' + (
            " for (let i = 0; i < 10; i++) { print(s); }"
        )
        error = fails_with(src, "output limit exceeded")
        assert error.partial_output  # what fit is kept

    def test_printing_one_huge_value_is_refused(self):
        src = 'let s = ""; for (let i = 0; i < 900; i++) { s = s + "p"; }' + (
            " let xs = [s, s, s]; print(xs);"
        )
        fails_with(src, "output limit exceeded")


class TestTime:
    def test_wall_clock_limit_stops_slow_programs(self):
        limits = RuntimeLimits(max_steps=50_000_000, max_seconds=0.2)
        fails_with("while (true) { }", "time limit exceeded", limits)


class TestNesting:
    @pytest.mark.parametrize(
        "source",
        [
            "print(" + "(" * 5000 + "1" + ")" * 5000 + ");",
            "print(" + "-" * 5000 + "1);",
            "print(" + "!" * 5000 + "true);",
            "print(1" + " + 1" * 5000 + ");",
            "let x = 0;" + "{" * 2000 + "x = 1;" + "}" * 2000,
            "let xs = " + "[" * 3000 + "]" * 3000 + ";",
        ],
        ids=["parens", "unary-minus", "not", "long-chain", "blocks", "arrays"],
    )
    def test_deep_nesting_is_a_syntax_error_not_a_crash(self, source):
        with pytest.raises(ParserError, match="nested too deeply"):
            analyze_source(source)

    def test_reasonable_nesting_still_works(self):
        src = "print(" + "(" * 100 + "1" + ")" * 100 + "); print(1" + " + 1" * 100 + ");"
        assert run_with(src, RuntimeLimits()) == ["1", "101"]

    @pytest.mark.parametrize("operation", [run_program, check_program, compile_program])
    def test_service_reports_deep_nesting_as_data(self, operation):
        result = operation("print(" + "(" * 5000 + "1" + ")" * 5000 + ");")
        assert result["ok"] is False
        assert "nested too deeply" in result["errors"][0]["message"]

    def test_self_containing_array_cannot_crash_printing(self):
        result = explore("let xs = []; push(xs, xs); print(xs);")
        assert result["ok"] is False
        assert result["failed_stage"] == "runtime"


class TestRecursionLimitIsThreadSafe:
    def test_concurrent_runs_restore_the_original_limit(self):
        original = sys.getrecursionlimit()
        program = "fn f(n) { if (n == 0) { return 0; } return f(n - 1); } print(f(200));"
        errors: list[BaseException] = []

        def worker():
            try:
                for _ in range(20):
                    assert run_with(program, RuntimeLimits()) == ["0"]
            except BaseException as exc:  # noqa: BLE001 - collect to assert in main thread
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert errors == []
        assert sys.getrecursionlimit() == original

    def test_limit_is_only_ever_raised_while_any_run_is_active(self):
        original = sys.getrecursionlimit()
        with python_recursion_limit(original + 5000):
            with python_recursion_limit(original + 100):
                assert sys.getrecursionlimit() >= original + 5000
            assert sys.getrecursionlimit() >= original + 5000
        assert sys.getrecursionlimit() == original


def test_playground_limits_are_tight_enough_for_a_shared_server():
    assert PLAYGROUND_LIMITS.max_string_length <= 100_000
    assert PLAYGROUND_LIMITS.max_output_chars <= 100_000
    assert PLAYGROUND_LIMITS.max_alloc_units <= 50_000_000
    assert PLAYGROUND_LIMITS.max_seconds is not None and PLAYGROUND_LIMITS.max_seconds <= 3


def test_errors_are_minilang_errors():
    # Callers catch MiniLangError; none of these may escape as a Python exception.
    assert issubclass(ParserError, MiniLangError)
