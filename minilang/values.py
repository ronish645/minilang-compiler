"""MiniLang value semantics: literals, operators and printing.

MiniLang values are represented by Python values (int, float, str, bool,
None, list for arrays), but Python's own rules must not leak through. For
example Python treats ``True`` as the integer 1, prints ``None`` and accepts
negative indexes; MiniLang does none of these.
"""

from __future__ import annotations

from typing import Any

from minilang.errors import MiniLangRuntimeError
from minilang.hints import IMMUTABLE_STRING_HINT, NEGATIVE_INDEX_HINT

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
    if isinstance(value, list):
        return "array"
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
        raise MiniLangRuntimeError(f"unknown literal type '{literal_type}'")
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
    if kind == "array":
        return "[" + ", ".join(format_element(v) for v in value) + "]"
    return str(value)


def format_element(value: Any) -> str:
    """Inside an array, strings are quoted so ["1"] and [1] print differently."""
    return f'"{value}"' if isinstance(value, str) else format_value(value)


def values_equal(left: Any, right: Any) -> bool:
    # Without this, Python would report true == 1.
    if isinstance(left, bool) != isinstance(right, bool):
        return False
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            values_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return left == right


def type_error(op: str, left: Any, right: Any) -> MiniLangRuntimeError:
    return MiniLangRuntimeError(f"cannot apply '{op}' to {type_name(left)} and {type_name(right)}")


def apply_arithmetic(op: str, left: Any, right: Any) -> Any:
    if op == "+" and isinstance(left, str) and isinstance(right, str):
        return left + right
    if not (is_number(left) and is_number(right)):
        raise type_error(op, left, right)
    if op in ("/", "%") and right == 0:
        raise MiniLangRuntimeError("division by zero")
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
    raise MiniLangRuntimeError(f"unknown operator '{op}'")


def negate(value: Any) -> Any:
    if not is_number(value):
        raise MiniLangRuntimeError(f"cannot apply unary '-' to {type_name(value)}")
    return -value


# ---- indexing ----------------------------------------------------------------
def check_index(container: Any, index: Any) -> None:
    kind = type_name(container)
    if kind not in ("array", "string"):
        raise MiniLangRuntimeError(f"cannot index a value of type {kind}")
    if type_name(index) != "int":
        raise MiniLangRuntimeError(f"index must be an int, got {type_name(index)}")
    if not 0 <= index < len(container):
        hint = NEGATIVE_INDEX_HINT if index < 0 else None
        raise MiniLangRuntimeError(
            f"index {index} out of range for {kind} of length {len(container)}", hint=hint
        )


def get_index(container: Any, index: Any) -> Any:
    check_index(container, index)
    return container[index]


def set_index(container: Any, index: Any, value: Any) -> None:
    if isinstance(container, str):
        raise MiniLangRuntimeError("strings are immutable", hint=IMMUTABLE_STRING_HINT)
    check_index(container, index)
    container[index] = value
