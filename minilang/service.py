"""Operations shared by every way of serving the compiler (MCP server, REST API).

Each function takes MiniLang source and returns plain, JSON-ready data. A
problem in the *program* is reported as data (``ok: False`` plus errors), never
raised: for a caller, a compile error is a normal result.
"""

from __future__ import annotations

from functools import cache
from pathlib import Path
from typing import Any

from minilang.diagnostics import format_diagnostic
from minilang.errors import MiniLangError
from minilang.pipeline import analyze_source, run_source
from minilang.playground import PLAYGROUND_LIMITS, error_list, explore
from minilang.runtime import RuntimeLimits

SPEC_PATH = Path(__file__).parent.parent / "docs" / "LANGUAGE_SPEC.md"
FILENAME = "program.ml"  # shown in diagnostics: " --> program.ml:3:7"


def run_program(source: str, limits: RuntimeLimits = PLAYGROUND_LIMITS) -> dict[str, Any]:
    """Compile and execute; output, every error (with hints) and the diagnostic text.

    Shared servers use tighter limits than the CLI: every runaway program costs CPU.
    """
    result = run_source(source, filename=FILENAME, limits=limits)
    return {
        "ok": result.ok,
        "output": result.output,
        "errors": error_list(result.exception) if result.exception else [],
        "diagnostic": result.diagnostic,
    }


def check_program(source: str) -> dict[str, Any]:
    """Lex, parse and type-check without running."""
    try:
        analyze_source(source)
    except MiniLangError as error:
        return {
            "ok": False,
            "errors": error_list(error),
            "diagnostic": format_diagnostic(error, source, FILENAME),
        }
    return {"ok": True, "errors": [], "diagnostic": None}


def compile_program(source: str, limits: RuntimeLimits = PLAYGROUND_LIMITS) -> dict[str, Any]:
    """Every compiler stage (tokens, AST, TAC, assembly, output) as structured data."""
    return explore(source, limits)


@cache
def language_spec() -> str:
    """The spec, read once. A server should call this at startup so a missing file fails fast."""
    return SPEC_PATH.read_text(encoding="utf-8")
