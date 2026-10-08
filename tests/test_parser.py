"""Parser unit tests: tokens -> AST shape and precedence."""

from minilang.ast_nodes import ASTNode
from minilang.lexer import Lexer
from minilang.parser import Parser


def parse(source: str) -> ASTNode:
    return Parser(Lexer(source).tokenize()).parse()


def expr(source: str) -> ASTNode:
    """Parse a single expression statement and return the expression."""
    return parse(source + ";").children[0].children[0]


def sexpr(node: ASTNode) -> str:
    """Compact s-expression rendering, e.g. (+ 1 (* 2 3))."""
    if node.kind in ("Literal", "Identifier"):
        return str(node.value)
    if node.kind == "Call":
        args = " ".join(sexpr(a) for a in node.children[1].children)
        return f"(call {node.children[0].value} {args})".replace(" )", ")")
    parts = " ".join(sexpr(c) for c in node.children)
    return f"({node.value} {parts})"


class TestPrecedence:
    def test_multiplication_binds_tighter_than_addition(self):
        assert sexpr(expr("1 + 2 * 3")) == "(+ 1 (* 2 3))"

    def test_parentheses_override_precedence(self):
        assert sexpr(expr("(1 + 2) * 3")) == "(* (+ 1 2) 3)"

    def test_subtraction_is_left_associative(self):
        assert sexpr(expr("10 - 3 - 2")) == "(- (- 10 3) 2)"

    def test_assignment_is_right_associative(self):
        assert sexpr(expr("a = b = 1")) == "(= a (= b 1))"

    def test_comparison_binds_tighter_than_logical(self):
        assert sexpr(expr("a < 1 && b > 2 || c")) == "(|| (&& (< a 1) (> b 2)) c)"

    def test_equality_binds_looser_than_comparison(self):
        assert sexpr(expr("a < b == c < d")) == "(== (< a b) (< c d))"

    def test_unary_operators(self):
        assert sexpr(expr("-a * !b")) == "(* (- a) (! b))"

    def test_postfix_increment(self):
        assert sexpr(expr("i++")) == "(++ i)"
        assert expr("i++").kind == "PostfixOp"

    def test_call_with_arguments(self):
        assert sexpr(expr("f(1, g(2))")) == "(call f 1 (call g 2))"

    def test_call_without_arguments(self):
        assert sexpr(expr("f()")) == "(call f)"


class TestStatements:
    def test_kinds_of_top_level_statements(self):
        program = parse(
            "let a = 1; const b = 2; print(a); if (true) {} while (false) {} "
            "for (;;) {} fn f() { return; } { } a = 3;"
        )
        assert [c.kind for c in program.children] == [
            "VarDecl", "VarDecl", "Print", "If", "While", "For",
            "FunctionDecl", "Block", "ExpressionStatement",
        ]  # fmt: skip

    def test_declaration_without_initializer(self):
        decl = parse("let a;").children[0]
        assert decl.value == "let"
        assert len(decl.children) == 1

    def test_else_if_chains_nest(self):
        node = parse("if (a) {} else if (b) {} else {}").children[0]
        assert len(node.children) == 3
        assert node.children[2].kind == "If"

    def test_for_with_empty_clauses(self):
        init, cond, update, _ = parse("for (;;) {}").children[0].children
        assert (init.kind, cond.kind, update.kind) == ("EmptyInit", "EmptyCondition", "EmptyUpdate")

    def test_for_with_expression_init(self):
        init = parse("let i; for (i = 0; i < 3; i++) {}").children[1].children[0]
        assert init.kind == "Assign"

    def test_function_parameters(self):
        fn = parse("fn add(a, b) { return a + b; }").children[0]
        assert fn.value == "add"
        assert [p.value for p in fn.children[0].children] == ["a", "b"]


class TestLiteralTypes:
    def test_each_literal_records_its_type(self):
        types = [expr(src).literal_type for src in ("1", "1.5", '"1"', "true", "null")]
        assert types == ["int", "float", "string", "bool", "null"]


class TestPositions:
    def test_binary_op_is_positioned_at_its_operator(self):
        node = expr("ab + cd")
        assert (node.line, node.col) == (1, 4)

    def test_statement_is_positioned_at_its_keyword(self):
        node = parse("\n  while (true) {}").children[0]
        assert (node.line, node.col) == (2, 3)


def test_pretty_prints_an_indented_tree():
    assert parse("print(1);").pretty() == "Program\n  Print\n    Literal: 1\n"
