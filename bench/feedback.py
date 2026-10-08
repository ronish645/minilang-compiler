"""The experimental variable: how much the compiler tells the model when code fails.

    oneshot     no tool at all; the model writes the program once, blind
    opaque      the tool only says that the program failed
    message     the error message, without stage or position
    diagnostic  stage, line/column, the source line and a caret (minilang's
                own format_diagnostic output)

Successful runs look the same in every condition: the printed output.
"""

from __future__ import annotations

from minilang.pipeline import RunResult

ONESHOT = "oneshot"
OPAQUE = "opaque"
MESSAGE = "message"
DIAGNOSTIC = "diagnostic"
CONDITIONS = (ONESHOT, OPAQUE, MESSAGE, DIAGNOSTIC)
TOOL_CONDITIONS = (OPAQUE, MESSAGE, DIAGNOSTIC)


def format_output(lines: list[str]) -> str:
    return "\n".join(lines) if lines else "(no output)"


def format_run_result(result: RunResult, condition: str) -> str:
    """What the model sees after calling run_minilang."""
    if result.ok:
        return f"The program ran successfully. Output:\n{format_output(result.output)}"

    if condition == OPAQUE:
        detail = "Error: the program failed."
    elif condition == MESSAGE:
        detail = f"Error: {result.error['message']}"
    elif condition == DIAGNOSTIC:
        detail = result.diagnostic or f"Error: {result.error['message']}"
        if result.output:
            detail += f"\n\nOutput printed before the error:\n{format_output(result.output)}"
    else:
        raise ValueError(f"no run feedback in condition {condition!r}")
    return detail
