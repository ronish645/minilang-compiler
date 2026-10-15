"""Built-ins added after the v2 review: abs, min, max, ord, chr, slice."""

import pytest

from minilang.errors import MiniLangRuntimeError, SemanticError


class TestNumeric:
    @pytest.mark.parametrize(
        ("call", "printed"),
        [
            ("abs(-7)", "7"),
            ("abs(2.5)", "2.5"),
            ("abs(0 - 1.5)", "1.5"),
            ("min(3, 9)", "3"),
            ("max(3, 9)", "9"),
            ("min(-2, -5)", "-5"),
            ("max(2, 1.5)", "2.0"),  # one float operand makes the result a float
            ("min(1, 2.5)", "1.0"),
        ],
    )
    def test_results(self, run, call, printed):
        assert run(f"print({call});") == [printed]

    def test_int_results_keep_the_int_type(self, run):
        src = 'let m = max(1, 2); m = "x";'
        with pytest.raises(SemanticError, match="cannot assign string to 'm' of type int"):
            run(src)

    def test_mixed_results_are_floats(self, run):
        assert run("let m = max(1, 2.0); m = 0.5; print(m);") == ["0.5"]

    @pytest.mark.parametrize(
        "src", ['abs("3");', "max(true, 1);", "min([1], 2);", "abs(1, 2);", "max(1);"]
    )
    def test_static_type_and_arity_errors(self, run, src):
        with pytest.raises(SemanticError):
            run(src)

    def test_runtime_type_errors_for_unknown_arguments(self, run):
        with pytest.raises(MiniLangRuntimeError, match="abs\\(\\) expects a number, got bool"):
            run("fn f(x) { return abs(x); } f(true);")


class TestCharacters:
    def test_ord_and_chr_round_trip(self, run):
        assert run('print(ord("A")); print(chr(97)); print(chr(ord("a") + 1));') == [
            "65",
            "a",
            "b",
        ]

    def test_caesar_shift_without_a_lookup_table(self, run):
        src = (
            'fn shift(s, k) { let out = "";'
            " for (let i = 0; i < len(s); i++) {"
            ' out = out + chr((ord(s[i]) - ord("a") + k) % 26 + ord("a")); }'
            ' return out; } print(shift("xyz", 3));'
        )
        assert run(src) == ["abc"]

    @pytest.mark.parametrize(
        ("src", "message"),
        [
            ('print(ord("ab"));', "ord\\(\\) expects a single character, got a string of length 2"),
            ('print(ord(""));', "got a string of length 0"),
            ("print(chr(-1));", "chr\\(\\) code -1 is out of range"),
            ("print(chr(1114112));", "out of range"),
        ],
    )
    def test_runtime_errors(self, run, src, message):
        with pytest.raises(MiniLangRuntimeError, match=message):
            run(src)

    @pytest.mark.parametrize("src", ["ord(65);", 'chr("a");', "chr(1.5);"])
    def test_static_type_errors(self, run, src):
        with pytest.raises(SemanticError):
            run(src)


class TestSlice:
    @pytest.mark.parametrize(
        ("call", "printed"),
        [
            ('slice("hello", 1, 4)', "ell"),
            ('slice("hello", 0, 0)', ""),
            ("slice([1, 2, 3, 4], 1, 3)", "[2, 3]"),
            ("slice([1, 2], 0, 2)", "[1, 2]"),
        ],
    )
    def test_results(self, run, call, printed):
        assert run(f"print({call});") == [printed]

    def test_slice_of_an_array_is_a_copy(self, run):
        src = "let a = [1, 2, 3]; let b = slice(a, 0, 3); b[0] = 9; print(a[0]);"
        assert run(src) == ["1"]

    def test_slice_keeps_the_static_type(self, run):
        with pytest.raises(SemanticError, match="arithmetic operator '-'"):
            run('let s = slice("abc", 0, 1); print(s - 1);')

    @pytest.mark.parametrize(
        ("src", "message"),
        [
            ('slice("abc", 2, 1);', "slice\\(\\) range 2..1 is out of bounds for length 3"),
            ('slice("abc", 0, 4);', "range 0..4 is out of bounds"),
            ("slice([1], -1, 1);", "range -1..1 is out of bounds"),
        ],
    )
    def test_out_of_bounds_is_an_error_not_clamped(self, run, src, message):
        with pytest.raises(MiniLangRuntimeError, match=message):
            run(src)

    @pytest.mark.parametrize("src", ["slice(5, 0, 1);", 'slice("a", "0", 1);', 'slice("a", 0);'])
    def test_static_errors(self, run, src):
        with pytest.raises(SemanticError):
            run(src)


@pytest.mark.parametrize("name", ["abs", "min", "max", "ord", "chr", "slice"])
def test_new_built_in_names_are_reserved(run, name):
    with pytest.raises(SemanticError, match="is a built-in function"):
        run(f"let {name} = 1;")
