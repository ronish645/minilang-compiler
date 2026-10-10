"""Recursive-descent parser: tokens -> AST.

Each grammar rule is one method. Expression precedence is encoded by the
call chain, lowest precedence first:

    assignment -> logical_or -> logical_and -> equality -> comparison
               -> term (+ -) -> factor (* / %) -> unary -> postfix -> primary

After a syntax error the parser records it, skips ahead to the next statement
("panic-mode recovery") and keeps going, so one run reports several errors.
"""

from __future__ import annotations

from minilang.ast_nodes import ASTNode
from minilang.errors import ErrorCollector, ParserError
from minilang.hints import syntax_hint
from minilang.lexer import Token

ASSIGNMENT_OPS = ("=", "+=", "-=", "*=", "/=")
EQUALITY_OPS = ("==", "!=", "===")
COMPARISON_OPS = ("<", ">", "<=", ">=")
TERM_OPS = ("+", "-")
FACTOR_OPS = ("*", "/", "%")
PREFIX_OPS = ("!", "-", "++", "--")
POSTFIX_OPS = ("++", "--")
LITERAL_TOKEN_TYPES = {"INT": "int", "FLOAT": "float", "STRING": "string"}
LITERAL_KEYWORD_TYPES = {"true": "bool", "false": "bool", "null": "null"}
TOKEN_TYPE_NAMES = {"IDENT": "an identifier", "KW": "a keyword", "OP": "an operator"}


def describe_token(tok: Token) -> str:
    return "end of input" if tok.type == "EOF" else f"'{tok.value}'"


def make_node(kind: str, at: Token | ASTNode, **fields) -> ASTNode:
    """Create an AST node positioned at ``at`` (a token or another node)."""
    return ASTNode(kind, line=at.line, col=at.col, **fields)


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.i = 0
        self.previous: Token | None = None
        self.errors = ErrorCollector()

    # ---- token helpers -----------------------------------------------------
    def current(self) -> Token:
        return self.tokens[self.i]

    def advance(self) -> Token:
        tok = self.current()
        if self.i < len(self.tokens) - 1:
            self.i += 1
        self.previous = tok
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
            expected = f"'{value}'" if value is not None else TOKEN_TYPE_NAMES.get(ttype, ttype)
            raise ParserError(
                f"expected {expected} but found {describe_token(tok)}",
                *self.error_position(value),
                hint=self.hint_for(tok, expected),
            )
        self.advance()
        return tok

    def error_position(self, expected_value: str | None) -> tuple[int, int]:
        """Where to report a missing token.

        A missing ';' is reported right after the previous token rather than
        at the next one, which may be on a later line: that is where the
        programmer needs to type it.
        """
        tok, prev = self.current(), self.previous
        if expected_value in (";", ")") and prev is not None and prev.line < tok.line:
            return prev.line, prev.col + len(prev.value)
        return tok.line, tok.col

    def hint_for(self, found: Token, expected: str | None) -> str | None:
        previous = self.previous.value if self.previous else None
        return syntax_hint(previous, found.value, expected)

    # ---- error recovery ----------------------------------------------------
    def statement_or_recover(self) -> ASTNode | None:
        """Parse one statement; on a syntax error, record it and skip ahead."""
        start = self.i
        try:
            return self.statement()
        except ParserError as error:
            self.errors.add(error)
            if self.errors.full:
                self.errors.raise_if_any()
            self.synchronize(start)
            return None

    def synchronize(self, start: int) -> None:
        """Skip the whole statement that failed, so its leftovers don't cause new errors.

        Rescans from the statement's first token, tracking bracket depth. The
        statement ends at a ';' outside brackets, or after the '}' that closes
        its body (continuing through an 'else'). A '}' that closes an outer
        block is left for that block.
        """
        self.i = start
        depth = 0
        while not self.check("EOF"):
            tok = self.current()
            if tok.type == "SEP" and tok.value in "([{":
                depth += 1
            elif tok.type == "SEP" and tok.value in ")]}":
                if depth == 0:
                    break  # belongs to an enclosing block
                depth -= 1
                if tok.value == "}" and depth == 0:
                    self.advance()
                    if not self.check("KW", "else"):
                        return
                    continue
            elif tok.type == "SEP" and tok.value == ";" and depth == 0:
                self.advance()
                return
            self.advance()
        if self.i == start:
            self.advance()  # always make progress (e.g. a stray '}')

    # ---- statements --------------------------------------------------------
    def parse(self) -> ASTNode:
        program = make_node("Program", self.current())
        while not self.check("EOF"):
            node = self.statement_or_recover()
            if node is not None:
                program.children.append(node)
        self.errors.raise_if_any()
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
                "break": self.loop_control,
                "continue": self.loop_control,
            }.get(tok.value)
            if handler is not None:
                return handler()

        if self.check("SEP", "{"):
            return self.block()

        expr = self.expression()
        self.expect("SEP", ";")
        return make_node("ExpressionStatement", tok, children=[expr])

    def block(self) -> ASTNode:
        node = make_node("Block", self.expect("SEP", "{"))
        while not self.check("SEP", "}"):
            if self.check("EOF"):
                raise ParserError(
                    "unclosed block: missing '}' for the '{' opened here", node.line, node.col
                )
            child = self.statement_or_recover()
            if child is not None:
                node.children.append(child)
        self.expect("SEP", "}")
        return node

    def loop_control(self) -> ASTNode:
        kw = self.advance()  # 'break' or 'continue'
        self.expect("SEP", ";")
        return make_node(kw.value.capitalize(), kw)

    def variable_declaration(self) -> ASTNode:
        kw = self.expect("KW")
        ident = self.expect("IDENT")
        init = self.expression() if self.match("OP", "=") else None
        self.expect("SEP", ";")
        name = make_node("Identifier", ident, value=ident.value)
        node = make_node("VarDecl", kw, value=kw.value, children=[name])
        if init is not None:
            node.children.append(init)
        return node

    def print_statement(self) -> ASTNode:
        kw = self.expect("KW", "print")
        expr = self.parenthesized_expression()
        self.expect("SEP", ";")
        return make_node("Print", kw, children=[expr])

    def if_statement(self) -> ASTNode:
        kw = self.expect("KW", "if")
        condition = self.parenthesized_expression()
        node = make_node("If", kw, children=[condition, self.statement()])
        if self.match("KW", "else"):
            node.children.append(self.statement())
        return node

    def while_statement(self) -> ASTNode:
        kw = self.expect("KW", "while")
        condition = self.parenthesized_expression()
        return make_node("While", kw, children=[condition, self.statement()])

    def parenthesized_expression(self) -> ASTNode:
        self.expect("SEP", "(")
        expr = self.expression()
        self.expect("SEP", ")")
        return expr

    def for_statement(self) -> ASTNode:
        kw = self.expect("KW", "for")
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
        return make_node(
            "For",
            kw,
            children=[
                init or ASTNode("EmptyInit"),
                condition or ASTNode("EmptyCondition"),
                update or ASTNode("EmptyUpdate"),
                body,
            ],
        )

    def function_declaration(self) -> ASTNode:
        kw = self.expect("KW", "fn")
        name = self.expect("IDENT").value
        params = make_node("Parameters", self.expect("SEP", "("))
        if not self.check("SEP", ")"):
            params.children.append(self.parameter())
            while self.match("SEP", ","):
                params.children.append(self.parameter())
        self.expect("SEP", ")")
        body = self.block()
        return make_node("FunctionDecl", kw, value=name, children=[params, body])

    def parameter(self) -> ASTNode:
        tok = self.expect("IDENT")
        return make_node("Identifier", tok, value=tok.value)

    def return_statement(self) -> ASTNode:
        kw = self.expect("KW", "return")
        if self.match("SEP", ";"):
            return make_node("Return", kw)
        expr = self.expression()
        self.expect("SEP", ";")
        return make_node("Return", kw, children=[expr])

    # ---- expressions (lowest precedence first) -----------------------------
    def expression(self) -> ASTNode:
        return self.assignment()

    def assignment(self) -> ASTNode:
        left = self.logical_or()
        if self.check_op(ASSIGNMENT_OPS):
            op = self.advance()
            right = self.assignment()  # right-associative: a = b = c
            return make_node("Assign", op, value=op.value, children=[left, right])
        return left

    def binary_left_assoc(self, ops: tuple[str, ...], operand) -> ASTNode:
        """Parse ``operand (op operand)*`` and fold it into a left-leaning tree."""
        node = operand()
        while self.check_op(ops):
            op = self.advance()
            node = make_node("BinaryOp", op, value=op.value, children=[node, operand()])
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
            op = self.advance()
            return make_node("UnaryOp", op, value=op.value, children=[self.unary()])
        return self.postfix()

    def postfix(self) -> ASTNode:
        node = self.primary()
        while True:
            if self.check("SEP", "["):
                bracket = self.advance()
                index = self.expression()
                self.expect("SEP", "]")
                node = make_node("Index", bracket, children=[node, index])
            elif self.check_op(POSTFIX_OPS):
                op = self.advance()
                node = make_node("PostfixOp", op, value=op.value, children=[node])
            else:
                return node

    def primary(self) -> ASTNode:
        tok = self.current()
        if tok.type in LITERAL_TOKEN_TYPES:
            self.advance()
            return make_node(
                "Literal", tok, value=tok.value, literal_type=LITERAL_TOKEN_TYPES[tok.type]
            )

        if tok.type == "KW" and tok.value in LITERAL_KEYWORD_TYPES:
            self.advance()
            return make_node(
                "Literal", tok, value=tok.value, literal_type=LITERAL_KEYWORD_TYPES[tok.value]
            )

        if tok.type == "IDENT":
            self.advance()
            node = make_node("Identifier", tok, value=tok.value)
            if self.match("SEP", "("):
                return self.call_arguments(node)
            return node

        if self.match("SEP", "("):
            expr = self.expression()
            self.expect("SEP", ")")
            return expr

        if self.check("SEP", "["):
            return self.array_literal()

        raise ParserError(
            f"expected an expression but found {describe_token(tok)}",
            tok.line,
            tok.col,
            hint=self.hint_for(tok, "an expression"),
        )

    def array_literal(self) -> ASTNode:
        node = make_node("ArrayLiteral", self.expect("SEP", "["))
        if not self.check("SEP", "]"):
            node.children.append(self.expression())
            while self.match("SEP", ","):
                if self.check("SEP", "]"):  # allow a trailing comma
                    break
                node.children.append(self.expression())
        self.expect("SEP", "]")
        return node

    def call_arguments(self, callee: ASTNode) -> ASTNode:
        args = make_node("Arguments", self.previous)
        if not self.check("SEP", ")"):
            args.children.append(self.expression())
            while self.match("SEP", ","):
                args.children.append(self.expression())
        self.expect("SEP", ")")
        return make_node("Call", callee, children=[callee, args])
