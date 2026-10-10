"""Built-in functions: len, push, pop, str, int.

Each built-in has a static rule (argument and result types, used by the
semantic analyzer) and a runtime implementation (used by the interpreter).
Keeping both here means the two can't drift apart.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from minilang.errors import MiniLangRuntimeError, SemanticError
from minilang.values import format_value, type_name

UNKNOWN = "unknown"

ARITY = {"len": 1, "push": 2, "pop": 1, "str": 1, "int": 1}
BUILTIN_NAMES = frozenset(ARITY)

# Which argument types each built-in accepts (checked statically and at run time).
SIZED = ("array", "string")
INT_CONVERTIBLE = ("int", "float", "string")
EXPECTED_TYPES = {
    "len": [SIZED],
    "push": [("array",), None],  # None: any type
    "pop": [("array",)],
    "str": [None],
    "int": [INT_CONVERTIBLE],
}
EXPECTATION_TEXT = {
    SIZED: "an array or string",
    ("array",): "an array",
    INT_CONVERTIBLE: "a number or string",
}
RESULT_TYPES = {"len": "int", "push": "null", "pop": UNKNOWN, "str": "string", "int": "int"}


def type_mismatch(name: str, position: int, allowed: tuple[str, ...], got: str) -> str:
    where = " as its first argument" if position == 0 and ARITY[name] > 1 else ""
    return f"{name}() expects {EXPECTATION_TEXT[allowed]}{where}, got {got}"


def check_builtin(name: str, arg_types: list[str]) -> str:
    """Static check of a built-in call; returns the result type."""
    if len(arg_types) != ARITY[name]:
        raise SemanticError(f"{name}() expects {ARITY[name]} argument(s), got {len(arg_types)}")
    for position, (allowed, got) in enumerate(zip(EXPECTED_TYPES[name], arg_types, strict=True)):
        if allowed is not None and got != UNKNOWN and got not in allowed:
            raise SemanticError(type_mismatch(name, position, allowed, got))
    return RESULT_TYPES[name]


# ---- runtime -----------------------------------------------------------------
def to_int(value: Any) -> int:
    if isinstance(value, float):
        return int(value)  # truncates toward zero
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            raise MiniLangRuntimeError(f"int() cannot convert {value!r} to an int") from None
    return value


def builtin_pop(xs: list) -> Any:
    if not xs:
        raise MiniLangRuntimeError("pop from an empty array")
    return xs.pop()


def builtin_push(xs: list, value: Any) -> None:
    xs.append(value)


IMPLEMENTATIONS: dict[str, Callable[..., Any]] = {
    "len": len,
    "push": builtin_push,
    "pop": builtin_pop,
    "str": format_value,
    "int": to_int,
}


def call_builtin(name: str, args: list[Any]) -> Any:
    for position, (allowed, value) in enumerate(zip(EXPECTED_TYPES[name], args, strict=True)):
        if allowed is not None and type_name(value) not in allowed:
            raise MiniLangRuntimeError(type_mismatch(name, position, allowed, type_name(value)))
    return IMPLEMENTATIONS[name](*args)
