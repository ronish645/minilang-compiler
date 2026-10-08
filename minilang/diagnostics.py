"""Render compiler errors with the offending source line and a caret, e.g.

error[semantic]: variable 'y' used before declaration
 --> prog.ml:2:7
  |
2 | print(y);
  |       ^
"""

from __future__ import annotations

from minilang.errors import MiniLangError


def source_line(source: str, line: int) -> str | None:
    lines = source.splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else None


def format_diagnostic(error: MiniLangError, source: str, filename: str = "<input>") -> str:
    header = f"error[{error.stage}]: {error.message}"
    if error.line is None:
        return header

    location = f"{filename}:{error.line}:{error.col}"
    text = source_line(source, error.line)
    if text is None:  # e.g. an error reported at end of input
        return f"{header}\n --> {location}"

    gutter = " " * len(str(error.line))
    # Tabs are kept so the caret lines up under the same visual column.
    padding = "".join("\t" if ch == "\t" else " " for ch in text[: max(error.col - 1, 0)])
    return "\n".join(
        [
            header,
            f"{gutter}--> {location}",
            f"{gutter} |",
            f"{error.line} | {text}",
            f"{gutter} | {padding}^",
        ]
    )
