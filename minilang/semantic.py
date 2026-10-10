"""Semantic analysis: checks a parsed program for meaning errors.

The analyzer walks the AST with a stack of scopes (a symbol table per block)
and infers a simple type for every expression. It rejects programs that are
grammatically valid but meaningless, e.g. using an undeclared variable,
reassigning a ``const``, or calling a function with the wrong arity.

It keeps going after an error (recording it and moving to the next
statement), so one run reports every independent mistake.
"""

from __future__ import annotations

from dataclasses import dataclass

from minilang.ast_nodes import ASTNode
from minilang.builtins import BUILTIN_NAMES, check_builtin
from minilang.errors import ErrorCollector, SemanticError
from minilang.hints import (
    FLOAT_ASSIGN_HINT,
    IMMUTABLE_STRING_HINT,
    STRING_CONCAT_HINT,
    did_you_mean,
)

ARITHMETIC_OPS = ("+", "-", "*", "/", "%")
COMPARISON_OPS = ("<", ">", "<=", ">=")
EQUALITY_OPS = ("==", "!=", "===")
LOGICAL_OPS = ("&&", "||")
COMPOUND_ASSIGN_OPS = ("+=", "-=", "*=", "/=")
INCREMENT_OPS = ("++", "--")

# Typing is *gradual*: function parameters, call results and array elements
# are "unknown" at compile time. An unknown operand is accepted wherever a
# concrete type would be, and any real mismatch is caught by the runtime.
UNKNOWN = "unknown"


@dataclass
class Symbol:
    name: str
    var_type: str
    kind: str  # "let" | "const" | "param" | "function"
    params: list[str] | None = None


class Scope:
    def __init__(self, parent: Scope | None = None):
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def declare(self, symbol: Symbol) -> None:
        if symbol.name in BUILTIN_NAMES:
            raise SemanticError(f"'{symbol.name}' is a built-in function and cannot be redefined")
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

    def visible(self) -> dict[str, Symbol]:
        """Every visible name, inner scopes shadowing outer ones."""
        chain: list[Scope] = []
        scope: Scope | None = self
        while scope is not None:
            chain.append(scope)
            scope = scope.parent
        merged: dict[str, Symbol] = {}
        for s in reversed(chain):
            merged.update(s.symbols)
        return merged


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
        hint = STRING_CONCAT_HINT if op == "+" and "string" in (left, right) else None
        raise SemanticError(
            f"arithmetic operator '{op}' requires numeric operands"
            f"{' (or two strings)' if op == '+' else ''}, got {left} and {right}",
            hint=hint,
        )
    if UNKNOWN in (left, right):
        return UNKNOWN
    if op == "/":
        return "float"
    return "float" if "float" in (left, right) else "int"


class SemanticAnalyzer:
    def __init__(self) -> None:
        self.current_scope = Scope()
        self.in_function = False
        self.loop_depth = 0
        self.errors = ErrorCollector()

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

    def analyze_statements(self, statements: list[ASTNode]) -> None:
        """Check each statement, recording errors instead of stopping at the first."""
        self.hoist_functions(statements)
        for statement in statements:
            try:
                self.analyze(statement)
            except SemanticError as error:
                self.errors.add(error)
                if self.errors.full:
                    self.errors.raise_if_any()

    def hoist_functions(self, statements: list[ASTNode]) -> None:
        """Declare a block's functions up front so they can call each other in any order."""
        for node in statements:
            if node.kind == "FunctionDecl" and node.value not in self.current_scope.symbols:
                params = [p.value for p in node.children[0].children]
                self.declare(Symbol(node.value, "function", "function", params), node)

    def declare(self, symbol: Symbol, node: ASTNode) -> None:
        """Declare a symbol, recording (rather than raising) a clash."""
        try:
            self.current_scope.declare(symbol)
        except SemanticError as error:
            error.attach_position(node.line, node.col)
            self.errors.add(error)

    def undeclared(self, name: str, verb: str = "used") -> SemanticError:
        hint = did_you_mean(name, self.current_scope.visible().keys() | BUILTIN_NAMES)
        return SemanticError(f"variable '{name}' {verb} before declaration", hint=hint)

    # ---- statements --------------------------------------------------------
    def visit_Program(self, node: ASTNode) -> None:
        self.analyze_statements(node.children)
        self.errors.raise_if_any()

    def visit_Block(self, node: ASTNode) -> None:
        self.enter_scope()
        self.analyze_statements(node.children)
        self.exit_scope()

    def visit_VarDecl(self, node: ASTNode) -> None:
        decl_kind = node.value
        var_name = node.children[0].value
        if len(node.children) == 1:
            if decl_kind == "const":
                raise SemanticError(f"const variable '{var_name}' must be initialized")
            self.current_scope.declare(Symbol(var_name, UNKNOWN, decl_kind))
            return
        try:
            expr_type = self.analyze(node.children[1])
        except SemanticError:
            # Still declare it, so later uses don't produce follow-on errors.
            self.declare(Symbol(var_name, UNKNOWN, decl_kind), node)
            raise
        self.current_scope.declare(Symbol(var_name, expr_type, decl_kind))

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

    def analyze_loop_body(self, body: ASTNode) -> None:
        self.loop_depth += 1
        try:
            self.analyze(body)
        finally:
            self.loop_depth -= 1

    def visit_While(self, node: ASTNode) -> None:
        self.require_bool_condition(node.children[0], "while")
        self.analyze_loop_body(node.children[1])

    def visit_For(self, node: ASTNode) -> None:
        self.enter_scope()
        try:
            init, cond, update, body = node.children
            if init.kind != "EmptyInit":
                self.analyze(init)
            if cond.kind != "EmptyCondition":
                self.require_bool_condition(cond, "for")
            if update.kind != "EmptyUpdate":
                self.analyze(update)
            self.analyze_loop_body(body)
        finally:
            self.exit_scope()

    def visit_Break(self, node: ASTNode) -> None:
        if not self.loop_depth:
            raise SemanticError("'break' outside a loop")

    def visit_Continue(self, node: ASTNode) -> None:
        if not self.loop_depth:
            raise SemanticError("'continue' outside a loop")

    def visit_FunctionDecl(self, node: ASTNode) -> None:
        params_node, body_node = node.children
        param_names = [p.value for p in params_node.children]
        if node.value not in self.current_scope.symbols:  # not hoisted (e.g. an if-branch)
            self.current_scope.declare(Symbol(node.value, "function", "function", param_names))

        self.enter_scope()
        outer = (self.in_function, self.loop_depth)
        self.in_function, self.loop_depth = True, 0  # break can't cross a function
        try:
            for param in params_node.children:
                self.declare(Symbol(param.value, UNKNOWN, "param"), param)
            self.analyze(body_node)
        finally:
            self.in_function, self.loop_depth = outer
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
            raise self.undeclared(node.value)
        return symbol.var_type

    def visit_Literal(self, node: ASTNode) -> str:
        return node.literal_type

    def visit_ArrayLiteral(self, node: ASTNode) -> str:
        for element in node.children:
            self.analyze(element)
        return "array"

    def visit_Index(self, node: ASTNode) -> str:
        target_type = self.analyze(node.children[0])
        index_type = self.analyze(node.children[1])
        if index_type not in ("int", UNKNOWN):
            raise SemanticError(f"index must be an int, got {index_type}")
        if target_type == "string":
            return "string"
        if target_type in ("array", UNKNOWN):
            return UNKNOWN
        raise SemanticError(f"cannot index a value of type {target_type}")

    def check_assignable(self, target: ASTNode, verb: str) -> Symbol | None:
        """Validate an assignment target; returns the variable's symbol (None for an index)."""
        if target.kind == "Index":
            if self.analyze(target.children[0]) == "string":
                raise SemanticError("strings are immutable", hint=IMMUTABLE_STRING_HINT)
            self.analyze(target)
            return None
        if target.kind != "Identifier":
            raise SemanticError("invalid assignment target")
        symbol = self.current_scope.lookup(target.value)
        if symbol is None:
            raise self.undeclared(target.value, "assigned" if verb == "reassigned" else "used")
        if symbol.kind == "const":
            raise SemanticError(f"const variable '{target.value}' cannot be {verb}")
        if symbol.kind == "function":
            raise SemanticError(f"'{target.value}' is a function and cannot be {verb}")
        return symbol

    def visit_Assign(self, node: ASTNode) -> str:
        op = node.value
        left, right = node.children
        symbol = self.check_assignable(left, "reassigned")
        right_type = self.analyze(right)
        current = symbol.var_type if symbol else UNKNOWN

        if op in COMPOUND_ASSIGN_OPS:
            return arithmetic_result_type(op[0], current, right_type)
        if symbol is None:
            return right_type
        if current in (UNKNOWN, "null"):
            symbol.var_type = right_type
        elif not compatible_types(current, right_type):
            hint = FLOAT_ASSIGN_HINT if (current, right_type) == ("int", "float") else None
            raise SemanticError(
                f"cannot assign {right_type} to '{left.value}' of type {current}", hint=hint
            )
        return symbol.var_type

    def visit_BinaryOp(self, node: ASTNode) -> str:
        op = node.value
        left_type = self.analyze(node.children[0])
        right_type = self.analyze(node.children[1])

        if op in ARITHMETIC_OPS:
            return arithmetic_result_type(op, left_type, right_type)

        if op in COMPARISON_OPS:
            if not (is_numeric_or_unknown(left_type) and is_numeric_or_unknown(right_type)):
                raise SemanticError(
                    f"comparison operator '{op}' requires numeric operands, "
                    f"got {left_type} and {right_type}"
                )
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

    def check_increment(self, node: ASTNode, label: str) -> str:
        target = node.children[0]
        if target.kind not in ("Identifier", "Index"):
            raise SemanticError(f"{label} requires a variable")
        self.check_assignable(target, "updated")
        target_type = self.analyze(target)
        if not is_numeric_or_unknown(target_type):
            raise SemanticError(f"{label} requires a numeric operand, got {target_type}")
        return target_type

    def visit_UnaryOp(self, node: ASTNode) -> str:
        op = node.value
        if op in INCREMENT_OPS:
            return self.check_increment(node, f"'{op}'")
        expr_type = self.analyze(node.children[0])
        if op == "!":
            if not is_bool_or_unknown(expr_type):
                raise SemanticError("'!' operator requires boolean operand")
            return "bool"
        if not is_numeric_or_unknown(expr_type):  # unary '-'
            raise SemanticError("unary '-' requires numeric operand")
        return expr_type

    def visit_PostfixOp(self, node: ASTNode) -> str:
        return self.check_increment(node, f"postfix '{node.value}'")

    def visit_Call(self, node: ASTNode) -> str:
        callee, args_node = node.children
        name = callee.value
        if name in BUILTIN_NAMES:
            return check_builtin(name, [self.analyze(arg) for arg in args_node.children])

        symbol = self.current_scope.lookup(name)
        if symbol is None or symbol.kind != "function":
            functions = {n for n, s in self.current_scope.visible().items() if s.kind == "function"}
            hint = did_you_mean(name, functions | BUILTIN_NAMES)
            raise SemanticError(f"'{name}' is not a declared function", hint=hint)
        if len(args_node.children) != len(symbol.params):
            raise SemanticError(
                f"function '{name}' expects {len(symbol.params)} "
                f"argument(s), got {len(args_node.children)}"
            )
        for arg in args_node.children:
            self.analyze(arg)
        return UNKNOWN
