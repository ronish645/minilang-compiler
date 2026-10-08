"""Code generation: AST -> three-address code (TAC) + stack-style pseudo-assembly.

TAC is an intermediate representation where every instruction has at most
one operator, e.g. ``a = b + c * d`` becomes::

    t1 = c * d
    t2 = b + t1
    a = t2

Control flow is lowered to labels and conditional jumps (``if_false ... goto``).
"""

from __future__ import annotations

from minilang.ast_nodes import ASTNode

OP_INSTRUCTIONS = {
    "+": "ADD",
    "-": "SUB",
    "*": "MUL",
    "/": "DIV",
    "%": "MOD",
    "<": "LT",
    ">": "GT",
    "<=": "LE",
    ">=": "GE",
    "==": "EQ",
    "!=": "NE",
    "===": "SEQ",
    "&&": "AND",
    "||": "OR",
}


def op_to_instr(op: str) -> str:
    return OP_INSTRUCTIONS.get(op, f"OP_{op}")


class CodeGenerator:
    def __init__(self) -> None:
        self.tac: list[str] = []
        self.pseudo: list[str] = []
        self.temp_count = 0
        self.label_count = 0

    def new_temp(self) -> str:
        self.temp_count += 1
        return f"t{self.temp_count}"

    def new_label(self, prefix: str = "L") -> str:
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def emit(self, tac: str, pseudo: str) -> None:
        """Emit one TAC instruction and its pseudo-assembly equivalent."""
        self.tac.append(tac)
        self.pseudo.append(pseudo)

    def emit_label(self, label: str) -> None:
        self.emit(f"label {label}", f"LABEL {label}")

    def emit_jump(self, label: str) -> None:
        self.emit(f"goto {label}", f"JMP {label}")

    def emit_jump_if_false(self, cond: str, label: str) -> None:
        self.emit(f"if_false {cond} goto {label}", f"JZ {cond}, {label}")

    def generate(self, node: ASTNode) -> tuple[list[str], list[str]]:
        self.visit(node)
        return self.tac, self.pseudo

    # ---- statements --------------------------------------------------------
    def visit(self, node: ASTNode) -> None:
        method = getattr(self, f"visit_{node.kind}", self.generic_visit)
        method(node)

    def generic_visit(self, node: ASTNode) -> None:
        for child in node.children:
            self.visit(child)

    def visit_VarDecl(self, node: ASTNode) -> None:
        name = node.children[0].value
        if len(node.children) > 1:
            value = self.gen_expr(node.children[1])
            self.emit(f"{name} = {value}", f"STORE {name}, {value}")
        else:
            self.emit(f"declare {name}", f"DECLARE {name}")

    def visit_Print(self, node: ASTNode) -> None:
        value = self.gen_expr(node.children[0])
        self.emit(f"print {value}", f"PRINT {value}")

    def visit_ExpressionStatement(self, node: ASTNode) -> None:
        self.gen_expr(node.children[0])

    def visit_If(self, node: ASTNode) -> None:
        cond = self.gen_expr(node.children[0])
        else_label = self.new_label("ELSE")
        end_label = self.new_label("ENDIF")
        self.emit_jump_if_false(cond, else_label)
        self.visit(node.children[1])
        self.emit_jump(end_label)
        self.emit_label(else_label)
        if len(node.children) > 2:
            self.visit(node.children[2])
        self.emit_label(end_label)

    def visit_While(self, node: ASTNode) -> None:
        start = self.new_label("WHILE")
        end = self.new_label("ENDWHILE")
        self.emit_label(start)
        cond = self.gen_expr(node.children[0])
        self.emit_jump_if_false(cond, end)
        self.visit(node.children[1])
        self.emit_jump(start)
        self.emit_label(end)

    def visit_For(self, node: ASTNode) -> None:
        init, cond, update, body = node.children
        start = self.new_label("FOR")
        end = self.new_label("ENDFOR")
        if init.kind != "EmptyInit":
            self.visit(init)
        self.emit_label(start)
        if cond.kind != "EmptyCondition":
            self.emit_jump_if_false(self.gen_expr(cond), end)
        self.visit(body)
        if update.kind != "EmptyUpdate":
            self.gen_expr(update)
        self.emit_jump(start)
        self.emit_label(end)

    def visit_FunctionDecl(self, node: ASTNode) -> None:
        name = node.value
        params = ", ".join(p.value for p in node.children[0].children)
        self.emit(f"func {name}({params})", f"FUNC {name} {params}")
        self.visit(node.children[1])
        self.emit(f"endfunc {name}", f"END_FUNC {name}")

    def visit_Return(self, node: ASTNode) -> None:
        if node.children:
            value = self.gen_expr(node.children[0])
            self.emit(f"return {value}", f"RET {value}")
        else:
            self.emit("return", "RET")

    # ---- expressions (each returns the name holding its result) ------------
    def gen_expr(self, node: ASTNode) -> str:
        method = getattr(self, f"expr_{node.kind}", None)
        if method is None:
            raise ValueError(f"Code generation not implemented for {node.kind}")
        return method(node)

    def expr_Literal(self, node: ASTNode) -> str:
        value = node.value
        if value in ("true", "false", "null"):
            return str(value)
        if isinstance(value, str):
            is_float_like = "." in value or "e" in value.lower()
            try:
                float(value) if is_float_like else int(value)
                return value
            except ValueError:
                return repr(value)
        return str(value)

    def expr_Identifier(self, node: ASTNode) -> str:
        return node.value

    def expr_Assign(self, node: ASTNode) -> str:
        left = node.children[0].value
        right = self.gen_expr(node.children[1])
        op = node.value
        if op == "=":
            self.emit(f"{left} = {right}", f"STORE {left}, {right}")
            return left
        base_op = op[0]  # "+=" -> "+"
        temp = self.new_temp()
        self.tac += [f"{temp} = {left} {base_op} {right}", f"{left} = {temp}"]
        self.pseudo += [f"LOAD {left}", f"LOAD {right}", op_to_instr(base_op), f"STORE {left}"]
        return left

    def expr_BinaryOp(self, node: ASTNode) -> str:
        left = self.gen_expr(node.children[0])
        right = self.gen_expr(node.children[1])
        temp = self.new_temp()
        self.tac.append(f"{temp} = {left} {node.value} {right}")
        self.pseudo += [f"LOAD {left}", f"LOAD {right}", op_to_instr(node.value), f"STORE {temp}"]
        return temp

    def expr_UnaryOp(self, node: ASTNode) -> str:
        expr = self.gen_expr(node.children[0])
        op = node.value
        if op in ("++", "--") and node.children[0].kind == "Identifier":
            sign = "+" if op == "++" else "-"
            temp = self.new_temp()
            self.tac += [f"{temp} = {expr} {sign} 1", f"{expr} = {temp}"]
            self.pseudo += [
                f"LOAD {expr}",
                "PUSH 1",
                "ADD" if sign == "+" else "SUB",
                f"STORE {expr}",
            ]
            return expr
        temp = self.new_temp()
        self.emit(f"{temp} = {op}{expr}", f"UNARY {op} {expr}")
        return temp

    def expr_PostfixOp(self, node: ASTNode) -> str:
        name = self.gen_expr(node.children[0])
        sign = "+" if node.value == "++" else "-"
        temp = self.new_temp()
        # The temp keeps the *old* value: x++ evaluates to x before incrementing.
        self.tac += [f"{temp} = {name}", f"{name} = {name} {sign} 1"]
        self.pseudo.append(f"STORE {name}, {name} {sign} 1")
        return temp

    def expr_Call(self, node: ASTNode) -> str:
        func_name = node.children[0].value
        args = node.children[1].children
        for arg in args:
            value = self.gen_expr(arg)
            self.emit(f"param {value}", f"PUSH {value}")
        temp = self.new_temp()
        self.emit(
            f"{temp} = call {func_name}, {len(args)}",
            f"CALL {func_name}, {len(args)} -> {temp}",
        )
        return temp
