"""Lexer unit tests: source text -> tokens."""

import pytest

from minilang.lexer import Lexer


def token_pairs(source: str) -> list[tuple[str, str]]:
    return [(t.type, t.value) for t in Lexer(source).tokenize()][:-1]  # drop EOF


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("let", [("KW", "let")]),
        ("letter", [("IDENT", "letter")]),  # keywords match whole words only
        ("_tmp1", [("IDENT", "_tmp1")]),
        ("42", [("INT", "42")]),
        ("3.14", [("FLOAT", "3.14")]),
        ("1e5", [("FLOAT", "1e5")]),
        ("2.5E-3", [("FLOAT", "2.5E-3")]),
        ('"hi"', [("STRING", "hi")]),
        ("'hi'", [("STRING", "hi")]),
    ],
)
def test_single_tokens(source, expected):
    assert token_pairs(source) == expected


@pytest.mark.parametrize(
    ("source", "op"),
    [("==", "=="), ("===", "==="), ("<=", "<="), ("++", "++"), ("+=", "+="), ("&&", "&&")],
)
def test_longest_operator_wins(source, op):
    # Maximal munch: "==" must not lex as "=" "=".
    assert token_pairs(source) == [("OP", op)]


def test_number_followed_by_dot_without_digit_is_not_a_float():
    assert token_pairs("1.") == [("INT", "1"), ("SEP", ".")]


def test_e_without_exponent_digits_is_an_identifier():
    assert token_pairs("1e") == [("INT", "1"), ("IDENT", "e")]


@pytest.mark.parametrize(
    ("source", "value"),
    [
        (r'"a\nb"', "a\nb"),
        (r'"tab\t"', "tab\t"),
        (r'"q\"q"', 'q"q'),
        (r'"back\\"', "back\\"),
        (r'"\x"', "\\x"),  # unknown escapes are kept literally
        ("'it''s'", "it's"),
    ],
)
def test_string_escapes(source, value):
    assert token_pairs(source) == [("STRING", value)]


def test_comments_are_skipped():
    source = "a // line comment\n/* block\ncomment */ b"
    assert token_pairs(source) == [("IDENT", "a"), ("IDENT", "b")]


def test_tracks_line_and_column():
    tokens = Lexer("let x;\n  print(x);").tokenize()
    positions = {(t.value, t.line, t.col) for t in tokens}
    assert ("let", 1, 1) in positions
    assert ("print", 2, 3) in positions


def test_ends_with_eof_token():
    assert Lexer("").tokenize()[-1].type == "EOF"


def test_lexical_table():
    lexer = Lexer('let a = 1; let b = "s";')
    lexer.tokenize()
    table = lexer.lexical_table()
    assert table["identifiers"] == ["a", "b"]
    assert table["constants"] == ["1", "s"]
    assert "let" in table["keywords"]
