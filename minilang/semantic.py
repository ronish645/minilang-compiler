"""Semantic analysis: checks a parsed program for meaning errors.

The analyzer walks the AST with a stack of scopes (a symbol table per block)
and infers a simple type for every expression. It rejects programs that are
grammatically valid but meaningless, e.g. using an undeclared variable,
reassigning a ``const``, or calling a function with the wrong arity.
"""

from __future__ import annotations

from dataclasses import dataclass

from minilang.ast_nodes import ASTNode
from minilang.errors import SemanticError

ARITHMETIC_OPS = ("+", "-", "*", "/", "%")
COMPARISON_OPS = ("<", ">", "<=", ">=")
EQUALITY_OPS = ("==", "!=", "===")
LOGICAL_OPS = ("&&", "||")
COMPOUND_ASSIGN_OPS = ("+=", "-=", "*=", "/=")


@dataclass
class Symbol:
    name: str
    var_type: str
    kind: str  # "let" | "const" | "param" | "function"
    initialized: bool = False
    params: list[str] | None = None


class Scope:
    def __init__(self, parent: Scope | None = None):
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def declare(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise SemanticError(f"'{symbol.name}' is already declared in this scope")
        self.symbols[symbol.name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        scope: Scope | None = self
        while scope is not None:
            if name in scope.symbols:
                return scope.symbols[name]
            scope = scope.parent
        return None


# Typing is *gradual*: function parameters and call results are "unknown"
# at compile time. An unknown operand is accepted wherever a concrete type
# would be, and any real mismatch is caught by the runtime instead.
UNKNOWN = "unknown"


def is_numeric_or_unknown(t: str) -> bool:
    return t in ("int", "float", UNKNOWN)


def is_bool_or_unknown(t: str) -> bool:
    return t in ("bool", UNKNOWN)


def compatible_types(target: str, value: str) -> bool:
    """Can a ``value``-typed expression be stored in / compared with ``target``?"""
    if UNKNOWN in (target, value) or "null" in (target, value):
        return True
    return target == value or (target == "float" and value == "int")


def arithmetic_result_type(op: str, left: str, right: str) -> str:
    if op == "+" and {left, right} <= {"string", UNKNOWN} and "string" in (left, right):
        return "string" if left == right else UNKNOWN
    if not (is_numeric_or_unknown(left) and is_numeric_or_unknown(right)):
        raise SemanticError(
            f"arithmetic operator '{op}' requires numeric operands"
            f"{' (or two strings)' if op == '+' else ''}, got {left} and {right}"
        )
    if UNKNOWN in (left, right):
        return UNKNOWN
    if op == "/":
        return "float"
    return "float" if "float" in (left, right) else "int"


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.global_scope = Scope()
        self.current_scope = self.global_scope
        self.in_function = False

    def enter_scope(self) -> None:
        self.current_scope = Scope(self.current_scope)

    def exit_scope(self) -> None:
        if self.current_scope.parent is not None:
            self.current_scope = self.current_scope.parent

    def analyze(self, node: ASTNode) -> str | None:
        method = getattr(self, f"visit_{node.kind}", self.generic_visit)
        try:
            return method(node)
        except SemanticError as error:
            # The innermost node being checked is the most precise location.
            error.attach_position(node.line, node.col)
            raise

    def generic_visit(self, node: ASTNode) -> None:
        for child in node.children:
            self.analyze(child)

    def lookup_mutable(self, name: str, op: str) -> Symbol:
        """Resolve a variable that is about to be modified by ``op``."""
        symbol = self.current_scope.lookup(name)
        if symbol is None:
            raise SemanticError(f"variable '{name}' used before declaration")
        if symbol.kind == "const":
            raise SemanticError(f"const variable '{name}' cannot be updated")
        return symbol

    # ---- statements --------------------------------------------------------
    def visit_Program(self, node: ASTNode) -> None:
        self.generic_visit(node)

    def visit_Block(self, node: ASTNode) -> None:
        self.enter_scope()
        self.generic_visit(node)
        self.exit_scope()

    def visit_VarDecl(self, node: ASTNode) -> None:
        decl_kind = node.value
        var_name = node.children[0].value
        if len(node.children) == 1:
            if decl_kind == "const":
                raise SemanticError(f"const variable '{var_name}' must be initialized")
            self.current_scope.declare(Symbol(var_name, UNKNOWN, decl_kind))
            return

        expr_type = self.analyze(node.children[1])
        self.current_scope.declare(Symbol(var_name, expr_type, decl_kind, initialized=True))

    def visit_Print(self, node: ASTNode) -> None:
        self.analyze(node.children[0])

    def visit_ExpressionStatement(self, node: ASTNode) -> None:
        self.analyze(node.children[0])

    def require_bool_condition(self, node: ASTNode, construct: str) -> None:
        cond_type = self.analyze(node)
        if not is_bool_or_unknown(cond_type):
            raise SemanticError(
                f"{construct} condition must be boolean, got {cond_type}", node.line, node.col
            )

    def visit_If(self, node: ASTNode) -> None:
        self.require_bool_condition(node.children[0], "if")
        for branch in node.children[1:]:
            self.analyze(branch)

    def visit_While(self, node: ASTNode) -> None:
        self.require_bool_condition(node.children[0], "while")
        self.analyze(node.children[1])

    def visit_For(self, node: ASTNode) -> None:
        self.enter_scope()
        init, cond, update, body = node.children
        if init.kind != "EmptyInit":
            self.analyze(init)
        if cond.kind != "EmptyCondition":
            self.require_bool_condition(cond, "for")
        if update.kind != "EmptyUpdate":
            self.analyze(update)
        self.analyze(body)
        self.exit_scope()

    def visit_FunctionDecl(self, node: ASTNode) -> None:
        params_node, body_node = node.children
        param_names = [p.value for p in params_node.children]
        # Declared before the body is analyzed so the function can call itself.
        self.current_scope.declare(
            Symbol(node.value, "function", "function", initialized=True, params=param_names)
        )

        self.enter_scope()
        outer_in_function = self.in_function
        self.in_function = True
        for param in param_names:
            self.current_scope.declare(Symbol(param, UNKNOWN, "param", initialized=True))
        self.analyze(body_node)
        self.in_function = outer_in_function
        self.exit_scope()

    def visit_Return(self, node: ASTNode) -> str:
        if not self.in_function:
            raise SemanticError("return statement outside function")
        if node.children:
            return self.analyze(node.children[0])
        return "null"

    # ---- expressions (each returns the inferred type) -----------------------
    def visit_Identifier(self, node: ASTNode) -> str:
        symbol = self.current_scope.lookup(node.value)
        if symbol is None:
            raise SemanticError(f"variable '{node.value}' used before declaration")
        return symbol.var_type

    def visit_Literal(self, node: ASTNode) -> str:
        return node.literal_type

    def visit_Assign(self, node: ASTNode) -> str | None:
        op = node.value
        left, right = node.children
        if left.kind != "Identifier":
            raise SemanticError("invalid assignment target")
        symbol = self.current_scope.lookup(left.value)
        if symbol is None:
            raise SemanticError(f"variable '{left.value}' assigned before declaration")
        if symbol.kind == "const":
            raise SemanticError(f"const variable '{left.value}' cannot be reassigned")

        right_type = self.analyze(right)
        if op == "=":
            if symbol.var_type in (UNKNOWN, "null"):
                symbol.var_type = right_type
            elif not compatible_types(symbol.var_type, right_type):
                raise SemanticError(
                    f"cannot assign {right_type} to '{left.value}' of type {symbol.var_type}"
                )
            symbol.initialized = True
            return symbol.var_type

        if op in COMPOUND_ASSIGN_OPS:
            return arithmetic_result_type(op[0], symbol.var_type, right_type)
        return None

    def visit_BinaryOp(self, node: ASTNode) -> str:
        op = node.value
        left_type = self.analyze(node.children[0])
        right_type = self.analyze(node.children[1])

        if op in ARITHMETIC_OPS:
            return arithmetic_result_type(op, left_type, right_type)

        if op in COMPARISON_OPS:
            if not (is_numeric_or_unknown(left_type) and is_numeric_or_unknown(right_type)):
                raise SemanticError(f"comparison operator '{op}' requires numeric operands")
            return "bool"

        if op in EQUALITY_OPS:
            if not (
                compatible_types(left_type, right_type) or compatible_types(right_type, left_type)
            ):
                raise SemanticError(f"cannot compare {left_type} with {right_type}")
            return "bool"

        if op in LOGICAL_OPS:
            if not (is_bool_or_unknown(left_type) and is_bool_or_unknown(right_type)):
                raise SemanticError(f"logical operator '{op}' requires boolean operands")
            return "bool"

        return UNKNOWN

    def visit_UnaryOp(self, node: ASTNode) -> str | None:
        op = node.value
        expr = node.children[0]
        expr_type = self.analyze(expr)

        if op == "!":
            if not is_bool_or_unknown(expr_type):
                raise SemanticError("'!' operator requires boolean operand")
            return "bool"

        if op == "-":
            if not is_numeric_or_unknown(expr_type):
                raise SemanticError("unary '-' requires numeric operand")
            return expr_type

        if op in ("++", "--"):
            if expr.kind != "Identifier":
                raise SemanticError(f"'{op}' requires a variable")
            self.lookup_mutable(expr.value, op)
            if not is_numeric_or_unknown(expr_type):
                raise SemanticError(f"'{op}' requires numeric operand")
            return expr_type
        return None

    def visit_PostfixOp(self, node: ASTNode) -> str:
        op = node.value
        expr = node.children[0]
        expr_type = self.analyze(expr)
        if expr.kind != "Identifier":
            raise SemanticError(f"postfix '{op}' requires a variable")
        self.lookup_mutable(expr.value, op)
        if not is_numeric_or_unknown(expr_type):
            raise SemanticError(f"postfix '{op}' requires numeric operand")
        return expr_type

    def visit_Call(self, node: ASTNode) -> str:
        callee, args_node = node.children
        symbol = self.current_scope.lookup(callee.value)
        if symbol is None or symbol.kind != "function":
            raise SemanticError(f"'{callee.value}' is not a declared function")
        if symbol.params is not None and len(args_node.children) != len(symbol.params):
            raise SemanticError(
                f"function '{callee.value}' expects {len(symbol.params)} "
                f"argument(s), got {len(args_node.children)}"
            )
        for arg in args_node.children:
            self.analyze(arg)
        return UNKNOWN
