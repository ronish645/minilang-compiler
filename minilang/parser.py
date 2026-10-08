"""Recursive-descent parser: tokens -> AST.

Each grammar rule is one method. Expression precedence is encoded by the
call chain, lowest precedence first:

    assignment -> logical_or -> logical_and -> equality -> comparison
               -> term (+ -) -> factor (* / %) -> unary -> postfix -> primary
"""

from __future__ import annotations

from minilang.ast_nodes import ASTNode
from minilang.errors import ParserError
from minilang.lexer import Token

ASSIGNMENT_OPS = ("=", "+=", "-=", "*=", "/=")
EQUALITY_OPS = ("==", "!=", "===")
COMPARISON_OPS = ("<", ">", "<=", ">=")
TERM_OPS = ("+", "-")
FACTOR_OPS = ("*", "/", "%")
PREFIX_OPS = ("!", "-", "++", "--")
POSTFIX_OPS = ("++", "--")


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0

    # ---- token helpers -----------------------------------------------------
    def current(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        tok = self.current()
        if self.i < len(self.tokens) - 1:
            self.i += 1
        return tok

    def check(self, ttype: str, value: str | None = None) -> bool:
        tok = self.current()
        return tok.type == ttype and (value is None or tok.value == value)

    def check_op(self, ops: tuple[str, ...]) -> bool:
        return self.current().type == "OP" and self.current().value in ops

    def match(self, ttype: str, value: str | None = None) -> bool:
        if not self.check(ttype, value):
            return False
        self.advance()
        return True

    def expect(self, ttype: str, value: str | None = None) -> Token:
        tok = self.current()
        if not self.check(ttype, value):
            expected = ttype if value is None else f"{ttype}('{value}')"
            raise ParserError(
                f"Syntax error at line {tok.line}, col {tok.col}: "
                f"expected {expected}, got {tok.type}('{tok.value}')"
            )
        self.advance()
        return tok

    # ---- statements --------------------------------------------------------
    def parse(self) -> ASTNode:
        program = ASTNode("Program")
        while not self.check("EOF"):
            program.children.append(self.statement())
        return program

    def statement(self) -> ASTNode:
        tok = self.current()
        if tok.type == "KW":
            handler = {
                "let": self.variable_declaration,
                "const": self.variable_declaration,
                "print": self.print_statement,
                "if": self.if_statement,
                "while": self.while_statement,
                "for": self.for_statement,
                "fn": self.function_declaration,
                "return": self.return_statement,
            }.get(tok.value)
            if handler is not None:
                return handler()

        if self.check("SEP", "{"):
            return self.block()

        expr = self.expression()
        self.expect("SEP", ";")
        return ASTNode("ExpressionStatement", children=[expr])

    def block(self) -> ASTNode:
        self.expect("SEP", "{")
        node = ASTNode("Block")
        while not self.check("SEP", "}"):
            if self.check("EOF"):
                tok = self.current()
                raise ParserError(f"Unclosed block at line {tok.line}, col {tok.col}")
            node.children.append(self.statement())
        self.expect("SEP", "}")
        return node

    def variable_declaration(self) -> ASTNode:
        kind = self.expect("KW").value
        ident = self.expect("IDENT").value
        init = self.expression() if self.match("OP", "=") else None
        self.expect("SEP", ";")
        node = ASTNode("VarDecl", value=kind, children=[ASTNode("Identifier", value=ident)])
        if init is not None:
            node.children.append(init)
        return node

    def print_statement(self) -> ASTNode:
        self.expect("KW", "print")
        self.expect("SEP", "(")
        expr = self.expression()
        self.expect("SEP", ")")
        self.expect("SEP", ";")
        return ASTNode("Print", children=[expr])

    def if_statement(self) -> ASTNode:
        self.expect("KW", "if")
        condition = self.parenthesized_expression()
        node = ASTNode("If", children=[condition, self.statement()])
        if self.match("KW", "else"):
            node.children.append(self.statement())
        return node

    def while_statement(self) -> ASTNode:
        self.expect("KW", "while")
        condition = self.parenthesized_expression()
        return ASTNode("While", children=[condition, self.statement()])

    def parenthesized_expression(self) -> ASTNode:
        self.expect("SEP", "(")
        expr = self.expression()
        self.expect("SEP", ")")
        return expr

    def for_statement(self) -> ASTNode:
        self.expect("KW", "for")
        self.expect("SEP", "(")

        init: ASTNode | None = None
        if self.check("KW", "let") or self.check("KW", "const"):
            init = self.variable_declaration()  # consumes its own ';'
        else:
            if not self.check("SEP", ";"):
                init = self.expression()
            self.expect("SEP", ";")

        condition = None if self.check("SEP", ";") else self.expression()
        self.expect("SEP", ";")

        update = None if self.check("SEP", ")") else self.expression()
        self.expect("SEP", ")")

        body = self.statement()
        return ASTNode(
            "For",
            children=[
                init or ASTNode("EmptyInit"),
                condition or ASTNode("EmptyCondition"),
                update or ASTNode("EmptyUpdate"),
                body,
            ],
        )

    def function_declaration(self) -> ASTNode:
        self.expect("KW", "fn")
        name = self.expect("IDENT").value
        self.expect("SEP", "(")
        params = ASTNode("Parameters")
        if not self.check("SEP", ")"):
            params.children.append(ASTNode("Identifier", value=self.expect("IDENT").value))
            while self.match("SEP", ","):
                params.children.append(ASTNode("Identifier", value=self.expect("IDENT").value))
        self.expect("SEP", ")")
        body = self.block()
        return ASTNode("FunctionDecl", value=name, children=[params, body])

    def return_statement(self) -> ASTNode:
        self.expect("KW", "return")
        if self.match("SEP", ";"):
            return ASTNode("Return")
        expr = self.expression()
        self.expect("SEP", ";")
        return ASTNode("Return", children=[expr])

    # ---- expressions (lowest precedence first) -----------------------------
    def expression(self) -> ASTNode:
        return self.assignment()

    def assignment(self) -> ASTNode:
        left = self.logical_or()
        if self.check_op(ASSIGNMENT_OPS):
            op = self.advance().value
            right = self.assignment()  # right-associative: a = b = c
            return ASTNode("Assign", value=op, children=[left, right])
        return left

    def binary_left_assoc(self, ops: tuple[str, ...], operand) -> ASTNode:
        """Parse ``operand (op operand)*`` and fold it into a left-leaning tree."""
        node = operand()
        while self.check_op(ops):
            op = self.advance().value
            node = ASTNode("BinaryOp", value=op, children=[node, operand()])
        return node

    def logical_or(self) -> ASTNode:
        return self.binary_left_assoc(("||",), self.logical_and)

    def logical_and(self) -> ASTNode:
        return self.binary_left_assoc(("&&",), self.equality)

    def equality(self) -> ASTNode:
        return self.binary_left_assoc(EQUALITY_OPS, self.comparison)

    def comparison(self) -> ASTNode:
        return self.binary_left_assoc(COMPARISON_OPS, self.term)

    def term(self) -> ASTNode:
        return self.binary_left_assoc(TERM_OPS, self.factor)

    def factor(self) -> ASTNode:
        return self.binary_left_assoc(FACTOR_OPS, self.unary)

    def unary(self) -> ASTNode:
        if self.check_op(PREFIX_OPS):
            op = self.advance().value
            return ASTNode("UnaryOp", value=op, children=[self.unary()])
        return self.postfix()

    def postfix(self) -> ASTNode:
        node = self.primary()
        while self.check_op(POSTFIX_OPS):
            node = ASTNode("PostfixOp", value=self.advance().value, children=[node])
        return node

    def primary(self) -> ASTNode:
        tok = self.current()
        if tok.type in ("INT", "FLOAT", "STRING"):
            self.advance()
            return ASTNode("Literal", value=tok.value)

        if tok.type == "KW" and tok.value in ("true", "false", "null"):
            self.advance()
            return ASTNode("Literal", value=tok.value)

        if tok.type == "IDENT":
            self.advance()
            node = ASTNode("Identifier", value=tok.value)
            if self.match("SEP", "("):
                return self.call_arguments(node)
            return node

        if self.match("SEP", "("):
            expr = self.expression()
            self.expect("SEP", ")")
            return expr

        raise ParserError(
            f"Syntax error at line {tok.line}, col {tok.col}: "
            f"unexpected token {tok.type}('{tok.value}')"
        )

    def call_arguments(self, callee: ASTNode) -> ASTNode:
        args = ASTNode("Arguments")
        if not self.check("SEP", ")"):
            args.children.append(self.expression())
            while self.match("SEP", ","):
                args.children.append(self.expression())
        self.expect("SEP", ")")
        return ASTNode("Call", children=[callee, args])
