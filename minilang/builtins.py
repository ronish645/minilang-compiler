"""Built-in functions: len, push, pop, str, int, abs, min, max, ord, chr, slice.

Each built-in has a static rule (argument and result types, used by the
semantic analyzer) and a runtime implementation (used by the interpreter).
Keeping both here means the two can't drift apart.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

from minilang.errors import MiniLangRuntimeError, SemanticError
from minilang.values import format_value, type_name

UNKNOWN = "unknown"

# Which argument types each built-in accepts (checked statically and at run time).
SIZED = ("array", "string")
INT_CONVERTIBLE = ("int", "float", "string")
NUMBER = ("int", "float")
INT = ("int",)
STRING = ("string",)
EXPECTED_TYPES: dict[str, list[tuple[str, ...] | None]] = {
    "len": [SIZED],
    "push": [("array",), None],  # None: any type
    "pop": [("array",)],
    "str": [None],
    "int": [INT_CONVERTIBLE],
    "abs": [NUMBER],
    "min": [NUMBER, NUMBER],
    "max": [NUMBER, NUMBER],
    "ord": [STRING],
    "chr": [INT],
    "slice": [SIZED, INT, INT],
}
ARITY = {name: len(expected) for name, expected in EXPECTED_TYPES.items()}
BUILTIN_NAMES = frozenset(EXPECTED_TYPES)
EXPECTATION_TEXT = {
    SIZED: "an array or string",
    ("array",): "an array",
    INT_CONVERTIBLE: "a number or string",
    NUMBER: "a number",
    INT: "an int",
    STRING: "a string",
}


def numeric_result(arg_types: list[str]) -> str:
    """abs/min/max: int if every argument is an int, float if any is a float."""
    if UNKNOWN in arg_types:
        return UNKNOWN
    return "float" if "float" in arg_types else "int"


def same_as_first(arg_types: list[str]) -> str:
    """slice: a slice of an array is an array, of a string a string."""
    return arg_types[0]


RESULT_TYPES: dict[str, str | Callable[[list[str]], str]] = {
    "len": "int",
    "push": "null",
    "pop": UNKNOWN,
    "str": "string",
    "int": "int",
    "abs": numeric_result,
    "min": numeric_result,
    "max": numeric_result,
    "ord": "int",
    "chr": "string",
    "slice": same_as_first,
}


def type_mismatch(name: str, position: int, allowed: tuple[str, ...], got: str) -> str:
    where = f" as argument {position + 1}" if ARITY[name] > 1 else ""
    return f"{name}() expects {EXPECTATION_TEXT[allowed]}{where}, got {got}"


def check_builtin(name: str, arg_types: list[str]) -> str:
    """Static check of a built-in call; returns the result type."""
    if len(arg_types) != ARITY[name]:
        raise SemanticError(f"{name}() expects {ARITY[name]} argument(s), got {len(arg_types)}")
    for position, (allowed, got) in enumerate(zip(EXPECTED_TYPES[name], arg_types, strict=True)):
        if allowed is not None and got != UNKNOWN and got not in allowed:
            raise SemanticError(type_mismatch(name, position, allowed, got))
    result = RESULT_TYPES[name]
    return result(arg_types) if callable(result) else result


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


def numeric(pick: Callable[[Any, Any], Any]) -> Callable[[Any, Any], Any]:
    """Wrap min/max so a float operand gives a float result, matching the static type."""

    def apply(a: Any, b: Any) -> Any:
        result = pick(a, b)
        return float(result) if isinstance(a, float) or isinstance(b, float) else result

    return apply


def builtin_ord(s: str) -> int:
    if len(s) != 1:
        raise MiniLangRuntimeError(
            f"ord() expects a single character, got a string of length {len(s)}"
        )
    return ord(s)


def builtin_chr(code: int) -> str:
    if not 0 <= code <= sys.maxunicode:
        raise MiniLangRuntimeError(f"chr() code {code} is out of range (0 to {sys.maxunicode})")
    return chr(code)


def builtin_slice(xs: list | str, start: int, end: int) -> list | str:
    # No clamping and no negative indexes: those are Python behaviours, not MiniLang's.
    if not 0 <= start <= end <= len(xs):
        raise MiniLangRuntimeError(
            f"slice() range {start}..{end} is out of bounds for length {len(xs)}"
        )
    return xs[start:end]  # a new list or string; the original is unchanged


IMPLEMENTATIONS: dict[str, Callable[..., Any]] = {
    "len": len,
    "push": builtin_push,
    "pop": builtin_pop,
    "str": format_value,
    "int": to_int,
    "abs": abs,
    "min": numeric(min),
    "max": numeric(max),
    "ord": builtin_ord,
    "chr": builtin_chr,
    "slice": builtin_slice,
}


def call_builtin(name: str, args: list[Any]) -> Any:
    for position, (allowed, value) in enumerate(zip(EXPECTED_TYPES[name], args, strict=True)):
        if allowed is not None and type_name(value) not in allowed:
            raise MiniLangRuntimeError(type_mismatch(name, position, allowed, type_name(value)))
    return IMPLEMENTATIONS[name](*args)
