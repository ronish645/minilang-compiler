"""The experimental variable: how much the compiler tells the model when code fails.

    oneshot     no tool at all; the model writes the program once, blind
    opaque      the tool only says that the program failed
    message     the first error's message, without stage or position
    diagnostic  the first error with stage, line/column, the source line and a
                caret (the v1 compiler's format)
    hint        every error found, each with its snippet and, where the
                compiler recognizes the mistake, a fix-it "help" line

Successful runs look the same in every condition: the printed output.
"""

from __future__ import annotations

from minilang.diagnostics import format_diagnostic
from minilang.pipeline import RunResult

FILENAME = "program.ml"

ONESHOT = "oneshot"
OPAQUE = "opaque"
MESSAGE = "message"
DIAGNOSTIC = "diagnostic"
HINT = "hint"
CONDITIONS = (ONESHOT, OPAQUE, MESSAGE, DIAGNOSTIC, HINT)
TOOL_CONDITIONS = (OPAQUE, MESSAGE, DIAGNOSTIC, HINT)


def format_output(lines: list[str]) -> str:
    return "\n".join(lines) if lines else "(no output)"


def format_run_result(result: RunResult, condition: str, code: str) -> str:
    """What the model sees after calling run_minilang(code)."""
    if result.ok:
        return f"The program ran successfully. Output:\n{format_output(result.output)}"

    if condition == OPAQUE:
        return "Error: the program failed."
    if condition == MESSAGE:
        return f"Error: {result.error['message']}"
    if condition not in (DIAGNOSTIC, HINT):
        raise ValueError(f"no run feedback in condition {condition!r}")

    full = condition == HINT
    detail = format_diagnostic(
        result.exception, code, FILENAME, include_hints=full, include_additional=full
    )
    if result.output:
        detail += f"\n\nOutput printed before the error:\n{format_output(result.output)}"
    return detail
