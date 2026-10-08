"""Exception hierarchy shared by every compiler stage.

Each stage raises its own subclass so callers can tell *where* a program
failed (lexing, parsing, semantic analysis or execution) while still being
able to catch everything with a single ``except MiniLangError``.
"""

from __future__ import annotations


class MiniLangError(Exception):
    """Base class for all errors reported about a MiniLang program."""


class LexerError(MiniLangError):
    pass


class ParserError(MiniLangError):
    pass


class SemanticError(MiniLangError):
    pass


class MiniLangRuntimeError(MiniLangError):
    pass
