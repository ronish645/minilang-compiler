"""Render compiler errors with the offending source line and a caret, e.g.

error[semantic]: variable 'totl' used before declaration
 --> prog.ml:2:7
  |
2 | print(totl);
  |       ^
  = help: did you mean 'total'?
"""

from __future__ import annotations

from minilang.errors import MiniLangError


def source_line(source: str, line: int) -> str | None:
    lines = source.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else None


def format_one(error: MiniLangError, source: str, filename: str, include_hint: bool) -> str:
    header = f"error[{error.stage}]: {error.message}"
    hint = f"\n  = help: {error.hint}" if include_hint and error.hint else ""
    if error.line is None:
        return header + hint

    location = f"{filename}:{error.line}:{error.col}"
    text = source_line(source, error.line)
    if text is None:  # e.g. an error reported at end of input
        return f"{header}\n --> {location}{hint}"

    gutter = " " * len(str(error.line))
    # Tabs are kept so the caret lines up under the same visual column.
    padding = "".join("\t" if ch == "\t" else " " for ch in text[: max(error.col - 1, 0)])
    lines = [
        header,
        f"{gutter}--> {location}",
        f"{gutter} |",
        f"{error.line} | {text}",
        f"{gutter} | {padding}^",
    ]
    return "\n".join(lines) + hint


def format_diagnostic(
    error: MiniLangError,
    source: str,
    filename: str = "<input>",
    *,
    include_hints: bool = True,
    include_additional: bool = True,
) -> str:
    """Render an error (and, by default, every further error found with it)."""
    errors = [error, *error.additional] if include_additional else [error]
    rendered = "\n\n".join(format_one(e, source, filename, include_hints) for e in errors)
    if include_additional and error.additional:
        rendered += f"\n\n{len(errors)} errors found."
    return rendered
