"""Semantic analyzer unit tests: which programs are accepted or rejected."""

import pytest

from minilang.errors import SemanticError
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.semantic import SemanticAnalyzer


def check(source: str) -> None:
    SemanticAnalyzer().analyze(Parser(Lexer(source).tokenize()).parse())


@pytest.mark.parametrize(
    "source",
    [
        "let a = 1; a = 2;",
        "let f = 1.5; f = 2;",  # int widens to float
        "let a; a = 1; a = 2;",  # untyped declaration takes the first assigned type
        "let n = null; n = 5;",  # null can later hold any value
        "let s = 'a'; s = s + 'b';",
        "let x = 1; { let x = 2; }",  # shadowing in an inner block
        "fn f() { return 1; } fn g() { return f(); }",
        "fn fact(n) { if (n <= 1) { return 1; } return n * fact(n - 1); }",
        "let i = 0; i += 1; i *= 2; i -= 1; i /= 2;",
        "let a = 1; print(a == 1 && a != 2 || !(a < 0));",
        "fn f(x) { return x; } print(f(1) + f(2) > 2);",
        "print(1 === 1);",
        "let t = true; print(t == false);",
        "let i = 0; ++i; --i; i--;",
    ],
)
def test_valid_programs_are_accepted(source):
    check(source)


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("print(x);", "used before declaration"),
        ("x = 1;", "assigned before declaration"),
        ("let a = 1; let a = 2;", "already declared"),
        ("const c;", "must be initialized"),
        ("const c = 1; c = 2;", "cannot be reassigned"),
        ("const c = 1; c++;", "cannot be updated"),
        ("const c = 1; ++c;", "cannot be updated"),
        ("let a = 1; a = 'x';", "cannot assign string"),
        ("let a = 1; a += 'x';", "requires numeric operands"),
        ("print(1 - 'x');", "requires numeric operands"),
        ("print('a' < 'b');", "comparison operator '<' requires numeric"),
        ("print(1 == 'x');", "cannot compare int with string"),
        ("print(1 && true);", "logical operator '&&' requires boolean"),
        ("print(!1);", "'!' operator requires boolean"),
        ("print(-'x');", "unary '-' requires numeric"),
        ("let s = 'x'; s++;", "requires numeric operand"),
        ("let s = 'x'; ++s;", "requires numeric operand"),
        ("print(1++);", "requires a variable"),
        ("print(++1);", "requires a variable"),
        ("1 = 2;", "invalid assignment target"),
        ("while (1) {}", "while condition must be boolean"),
        ("for (; 'x'; ) {}", "for condition must be boolean"),
        ("let f = 1; f();", "not a declared function"),
        ("fn f(a) {} f();", "expects 1 argument(s), got 0"),
        ("return;", "outside function"),
        ("{ let inner = 1; } print(inner);", "used before declaration"),
        ("for (let i = 0; i < 1; i++) {} print(i);", "used before declaration"),
    ],
)
def test_invalid_programs_are_rejected(source, message):
    with pytest.raises(SemanticError, match=message.replace("(", r"\(").replace(")", r"\)")):
        check(source)
