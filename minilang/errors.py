"""Exception hierarchy shared by every compiler stage.

Each stage raises its own subclass so callers can tell *where* a program
failed (lexing, parsing, semantic analysis or execution) while still being
able to catch everything with a single ``except MiniLangError``.

Errors carry a bare ``message`` plus an optional source position, so they can
be rendered for humans (see ``diagnostics.py``) or serialized for tools/LLMs
(see ``to_dict``).
"""

from __future__ import annotations

from typing import Any, ClassVar


class MiniLangError(Exception):
    """Base class for all errors reported about a MiniLang program."""

    stage: ClassVar[str] = "error"

    def __init__(self, message: str, line: int | None = None, col: int | None = None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col

    def __str__(self) -> str:
        where = f" at line {self.line}, col {self.col}" if self.line is not None else ""
        return f"{self.stage.capitalize()} error{where}: {self.message}"

    def attach_position(self, line: int, col: int) -> None:
        """Record a position unless a more specific one was already set."""
        if self.line is None and line:
            self.line, self.col = line, col

    def to_dict(self) -> dict[str, Any]:
        return {"stage": self.stage, "message": self.message, "line": self.line, "col": self.col}


class LexerError(MiniLangError):
    stage = "lexer"


class ParserError(MiniLangError):
    stage = "syntax"


class SemanticError(MiniLangError):
    stage = "semantic"


class MiniLangRuntimeError(MiniLangError):
    stage = "runtime"

    def __init__(self, message: str, line: int | None = None, col: int | None = None):
        super().__init__(message, line, col)
        # Lines printed before the failure; useful when debugging a crash.
        self.partial_output: list[str] = []
