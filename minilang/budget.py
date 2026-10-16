"""Per-run resource accounting: the checks that stop memory, output and time bombs.

The step limit stops infinite loops, but a short loop can still exhaust memory:
doubling a string 40 times makes a terabyte, squaring an int 40 times makes a
number with trillions of digits. So sizes are checked **before** a value is
built, and every string or array allocation is charged to a per-run budget.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

from minilang.errors import MiniLangRuntimeError
from minilang.values import format_bounded, type_name

if TYPE_CHECKING:
    from minilang.runtime import RuntimeLimits

GROWING_INT_OPS = ("+", "-", "*")
TIME_CHECK_INTERVAL = 1024  # steps between clock reads (reading the clock isn't free)


def is_int(value: Any) -> bool:
    return type_name(value) == "int"  # excludes bool, which Python treats as an int


class Budget:
    def __init__(self, limits: RuntimeLimits):
        self.limits = limits
        self.allocated = 0  # characters + array elements created so far
        self.output_chars = 0
        self.started = time.monotonic()

    # ---- before an operation builds its result ---------------------------------
    def check_binary(self, op: str, left: Any, right: Any) -> None:
        if op == "+" and isinstance(left, str) and isinstance(right, str):
            self.charge_string(len(left) + len(right))
        elif op in GROWING_INT_OPS and is_int(left) and is_int(right):
            bits = (
                left.bit_length() + right.bit_length()
                if op == "*"
                else max(left.bit_length(), right.bit_length()) + 1
            )
            if bits > self.limits.max_int_bits:
                raise MiniLangRuntimeError(
                    f"integer too large (over {self.limits.max_int_bits} bits)"
                )

    def check_push(self, array: list) -> None:
        if len(array) + 1 > self.limits.max_array_length:
            raise MiniLangRuntimeError(
                f"array too long (limit {self.limits.max_array_length} elements)"
            )
        self.charge(1)

    def to_text(self, value: Any) -> str:
        """str(x): refuse before building text longer than the string limit."""
        text = format_bounded(value, self.limits.max_string_length)
        self.charge(len(text))
        return text

    # ---- after an operation (results bounded by their inputs) ------------------
    def charge_result(self, value: Any) -> None:
        if isinstance(value, str):
            self.charge_string(len(value))
        elif type_name(value) == "array":
            if len(value) > self.limits.max_array_length:
                raise MiniLangRuntimeError(
                    f"array too long (limit {self.limits.max_array_length} elements)"
                )
            self.charge(len(value))

    def charge_string(self, length: int) -> None:
        if length > self.limits.max_string_length:
            raise MiniLangRuntimeError(
                f"string too long ({length} characters; limit {self.limits.max_string_length})"
            )
        self.charge(length)

    def charge(self, units: int) -> None:
        self.allocated += units
        if self.allocated > self.limits.max_alloc_units:
            raise MiniLangRuntimeError(
                f"memory limit exceeded (the program created over "
                f"{self.limits.max_alloc_units} characters and array elements)"
            )

    # ---- output and time ---------------------------------------------------------
    def output_line(self, value: Any) -> str:
        remaining = self.limits.max_output_chars - self.output_chars
        try:
            text = format_bounded(value, remaining)
        except MiniLangRuntimeError:
            raise MiniLangRuntimeError(
                f"output limit exceeded ({self.limits.max_output_chars} characters)"
            ) from None
        self.output_chars += len(text) + 1  # + the newline
        return text

    def check_time(self, steps: int) -> None:
        if self.limits.max_seconds is None or steps % TIME_CHECK_INTERVAL:
            return
        if time.monotonic() - self.started > self.limits.max_seconds:
            raise MiniLangRuntimeError(
                f"time limit exceeded ({self.limits.max_seconds:g} s); is there an infinite loop?"
            )
