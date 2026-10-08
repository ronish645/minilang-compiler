"""Tree-walking interpreter: executes the AST directly.

Variables live in ``Environment`` objects chained to their parent scope.
Functions capture the environment they were defined in (a closure), and
``return`` is implemented by raising ``ReturnSignal`` to unwind the call.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from minilang.ast_nodes import ASTNode
from minilang.errors import MiniLangRuntimeError


class ReturnSignal(Exception):
    """Control-flow signal (not an error) used to unwind out of a function body."""

    def __init__(self, value: Any):
        super().__init__()
        self.value = value


@dataclass
class Binding:
    value: Any
    mutable: bool


class Environment:
    def __init__(self, parent: Environment | None = None):
        self.parent = parent
        self.values: dict[str, Binding] = {}

    def define(self, name: str, value: Any, mutable: bool = True) -> None:
        if name in self.values:
            raise MiniLangRuntimeError(f"Runtime error: '{name}' already defined in this scope")
        self.values[name] = Binding(value, mutable)

    def resolve(self, name: str) -> Binding:
        env: Environment | None = self
        while env is not None:
            if name in env.values:
                return env.values[name]
            env = env.parent
        raise MiniLangRuntimeError(f"Runtime error: undefined variable '{name}'")

    def assign(self, name: str, value: Any) -> None:
        binding = self.resolve(name)
        if not binding.mutable:
            raise MiniLangRuntimeError(
                f"Runtime error: const variable '{name}' cannot be reassigned"
            )
        binding.value = value


@dataclass
class UserFunction:
    name: str
    params: list[str]
    body: ASTNode
    closure: Environment


def literal_value(value: Any) -> Any:
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "null":
        return None
    if isinstance(value, str):
        try:
            if "." in value or "e" in value.lower():
                return float(value)
            return int(value)
        except ValueError:
            return value
    return value


def apply_binary(op: str, left: Any, right: Any) -> Any:
    operations = {
        "+": lambda: left + right,
        "-": lambda: left - right,
        "*": lambda: left * right,
        "/": lambda: left / right,
        "%": lambda: left % right,
        "<": lambda: left < right,
        ">": lambda: left > right,
        "<=": lambda: left <= right,
        ">=": lambda: left >= right,
        "==": lambda: left == right,
        "!=": lambda: left != right,
        "===": lambda: type(left) is type(right) and left == right,
        "&&": lambda: bool(left) and bool(right),
        "||": lambda: bool(left) or bool(right),
    }
    if op not in operations:
        raise MiniLangRuntimeError(f"Runtime error: unknown operator '{op}'")
    return operations[op]()


class MiniRuntime:
    def __init__(self) -> None:
        self.global_env = Environment()
        self.output: list[str] = []

    def run(self, node: ASTNode) -> list[str]:
        self.exec_stmt(node, self.global_env)
        return self.output

    # ---- statements --------------------------------------------------------
    def exec_stmt(self, node: ASTNode, env: Environment) -> None:
        method = getattr(self, f"exec_{node.kind}", None)
        if method is None:
            raise MiniLangRuntimeError(f"Runtime error: unsupported statement '{node.kind}'")
        method(node, env)

    def exec_Program(self, node: ASTNode, env: Environment) -> None:
        for child in node.children:
            self.exec_stmt(child, env)

    def exec_Block(self, node: ASTNode, env: Environment) -> None:
        block_env = Environment(env)
        for child in node.children:
            self.exec_stmt(child, block_env)

    def exec_VarDecl(self, node: ASTNode, env: Environment) -> None:
        name = node.children[0].value
        value = self.eval_expr(node.children[1], env) if len(node.children) > 1 else None
        env.define(name, value, mutable=(node.value != "const"))

    def exec_Print(self, node: ASTNode, env: Environment) -> None:
        self.output.append(str(self.eval_expr(node.children[0], env)))

    def exec_ExpressionStatement(self, node: ASTNode, env: Environment) -> None:
        self.eval_expr(node.children[0], env)

    def exec_If(self, node: ASTNode, env: Environment) -> None:
        if self.eval_expr(node.children[0], env):
            self.exec_stmt(node.children[1], env)
        elif len(node.children) > 2:
            self.exec_stmt(node.children[2], env)

    def exec_While(self, node: ASTNode, env: Environment) -> None:
        cond, body = node.children
        while self.eval_expr(cond, env):
            self.exec_stmt(body, env)

    def exec_For(self, node: ASTNode, env: Environment) -> None:
        loop_env = Environment(env)  # the loop variable is scoped to the loop
        init, cond, update, body = node.children
        if init.kind == "VarDecl":
            self.exec_stmt(init, loop_env)
        elif init.kind != "EmptyInit":
            self.eval_expr(init, loop_env)
        while cond.kind == "EmptyCondition" or self.eval_expr(cond, loop_env):
            self.exec_stmt(body, loop_env)
            if update.kind != "EmptyUpdate":
                self.eval_expr(update, loop_env)

    def exec_FunctionDecl(self, node: ASTNode, env: Environment) -> None:
        params = [p.value for p in node.children[0].children]
        func = UserFunction(node.value, params, node.children[1], env)
        env.define(node.value, func, mutable=False)

    def exec_Return(self, node: ASTNode, env: Environment) -> None:
        value = self.eval_expr(node.children[0], env) if node.children else None
        raise ReturnSignal(value)

    # ---- expressions -------------------------------------------------------
    def eval_expr(self, node: ASTNode, env: Environment) -> Any:
        method = getattr(self, f"eval_{node.kind}", None)
        if method is None:
            raise MiniLangRuntimeError(f"Runtime error: unsupported expression '{node.kind}'")
        return method(node, env)

    def eval_Literal(self, node: ASTNode, env: Environment) -> Any:
        return literal_value(node.value)

    def eval_Identifier(self, node: ASTNode, env: Environment) -> Any:
        return env.resolve(node.value).value

    def eval_Assign(self, node: ASTNode, env: Environment) -> Any:
        name = node.children[0].value
        right = self.eval_expr(node.children[1], env)
        result = (
            right
            if node.value == "="
            else apply_binary(node.value[0], env.resolve(name).value, right)
        )
        env.assign(name, result)
        return result

    def eval_BinaryOp(self, node: ASTNode, env: Environment) -> Any:
        left = self.eval_expr(node.children[0], env)
        right = self.eval_expr(node.children[1], env)
        return apply_binary(node.value, left, right)

    def eval_UnaryOp(self, node: ASTNode, env: Environment) -> Any:
        op = node.value
        child = node.children[0]
        value = self.eval_expr(child, env)
        if op == "!":
            return not value
        if op == "-":
            return -value
        if child.kind != "Identifier":
            raise MiniLangRuntimeError(f"Runtime error: '{op}' requires identifier")
        new_value = value + 1 if op == "++" else value - 1
        env.assign(child.value, new_value)
        return new_value

    def eval_PostfixOp(self, node: ASTNode, env: Environment) -> Any:
        child = node.children[0]
        if child.kind != "Identifier":
            raise MiniLangRuntimeError(f"Runtime error: postfix '{node.value}' requires identifier")
        old_value = env.resolve(child.value).value
        env.assign(child.value, old_value + 1 if node.value == "++" else old_value - 1)
        return old_value

    def eval_Call(self, node: ASTNode, env: Environment) -> Any:
        func_name = node.children[0].value
        func = env.resolve(func_name).value
        if not isinstance(func, UserFunction):
            raise MiniLangRuntimeError(f"Runtime error: '{func_name}' is not callable")
        args = [self.eval_expr(arg, env) for arg in node.children[1].children]
        return self.call_function(func, args)

    def call_function(self, func: UserFunction, args: list[Any]) -> Any:
        if len(args) != len(func.params):
            raise MiniLangRuntimeError(
                f"Runtime error: function '{func.name}' expects {len(func.params)} "
                f"argument(s), got {len(args)}"
            )
        call_env = Environment(func.closure)
        for name, value in zip(func.params, args, strict=True):
            call_env.define(name, value)
        try:
            self.exec_stmt(func.body, call_env)
        except ReturnSignal as signal:
            return signal.value
        return None
