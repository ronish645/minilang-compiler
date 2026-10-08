"""MiniLang value semantics: literals, operators and printing.

MiniLang values are represented by Python values (int, float, str, bool,
None), but Python's own rules must not leak through. For example Python
treats ``True`` as the integer 1 and prints ``None``; MiniLang does neither.
"""

from __future__ import annotations

from typing import Any

from minilang.errors import MiniLangRuntimeError

ARITHMETIC_OPS = frozenset({"+", "-", "*", "/", "%"})
COMPARISON_OPS = frozenset({"<", ">", "<=", ">="})


def type_name(value: Any) -> str:
    if isinstance(value, bool):  # checked first: bool is a subclass of int
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if value is None:
        return "null"
    return "function"


def is_number(value: Any) -> bool:
    return type_name(value) in ("int", "float")


def literal_value(text: str, literal_type: str | None) -> Any:
    """Convert a Literal node's source text into a runtime value."""
    converters = {
        "int": int,
        "float": float,
        "string": str,
        "bool": lambda t: t == "true",
        "null": lambda _: None,
    }
    if literal_type not in converters:
        raise MiniLangRuntimeError(f"Runtime error: unknown literal type '{literal_type}'")
    return converters[literal_type](text)


def format_value(value: Any) -> str:
    """How ``print`` displays a value."""
    kind = type_name(value)
    if kind == "bool":
        return "true" if value else "false"
    if kind == "null":
        return "null"
    if kind == "function":
        return f"<fn {value.name}>"
    return str(value)


def values_equal(left: Any, right: Any) -> bool:
    # Without this, Python would report true == 1.
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    return left == right


def type_error(op: str, left: Any, right: Any) -> MiniLangRuntimeError:
    return MiniLangRuntimeError(
        f"Runtime error: cannot apply '{op}' to {type_name(left)} and {type_name(right)}"
    )


def apply_arithmetic(op: str, left: Any, right: Any) -> Any:
    if op == "+" and isinstance(left, str) and isinstance(right, str):
        return left + right
    if not (is_number(left) and is_number(right)):
        raise type_error(op, left, right)
    if op in ("/", "%") and right == 0:
        raise MiniLangRuntimeError("Runtime error: division by zero")
    operations = {
        "+": lambda: left + right,
        "-": lambda: left - right,
        "*": lambda: left * right,
        "/": lambda: left / right,
        "%": lambda: left % right,
    }
    return operations[op]()


def apply_binary(op: str, left: Any, right: Any) -> Any:
    if op in ARITHMETIC_OPS:
        return apply_arithmetic(op, left, right)
    if op in COMPARISON_OPS:
        if not (is_number(left) and is_number(right)):
            raise type_error(op, left, right)
        comparisons = {
            "<": lambda: left < right,
            ">": lambda: left > right,
            "<=": lambda: left <= right,
            ">=": lambda: left >= right,
        }
        return comparisons[op]()
    if op == "==":
        return values_equal(left, right)
    if op == "!=":
        return not values_equal(left, right)
    if op == "===":
        return type_name(left) == type_name(right) and left == right
    if op == "&&":
        return bool(left) and bool(right)
    if op == "||":
        return bool(left) or bool(right)
    raise MiniLangRuntimeError(f"Runtime error: unknown operator '{op}'")


def negate(value: Any) -> Any:
    if not is_number(value):
        raise MiniLangRuntimeError(f"Runtime error: cannot apply unary '-' to {type_name(value)}")
    return -value
