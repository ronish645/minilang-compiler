"""Fix-it hints: recognize habits from other languages and suggest the MiniLang way.

Most mistakes people (and language models) make in a new language are
carry-overs: writing ``xs.length``, ``var x``, ``True`` or ``x % 2 == 0 ? a : b``.
Naming the habit is more useful than a generic "unexpected token".
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable

BUILTIN_HINT = "built-ins are len(x), push(xs, v), pop(xs), str(x) and int(x)"

# Identifiers that are keywords or functions in other languages.
FOREIGN_NAMES = {
    "function": "functions are declared with fn: fn name(a, b) { ... }",
    "def": "functions are declared with fn: fn name(a, b) { ... }",
    "func": "functions are declared with fn: fn name(a, b) { ... }",
    "var": "declare variables with let (or const)",
    "elif": "use else if",
    "elsif": "use else if",
    "True": "booleans are lowercase: true / false",
    "False": "booleans are lowercase: true / false",
    "None": "MiniLang's empty value is null",
    "nil": "MiniLang's empty value is null",
    "undefined": "MiniLang's empty value is null",
    "console": "print a value with print(x)",
    "println": "print a value with print(x)",
    "printf": "print a value with print(x); build text with + and str(n)",
    "length": f"use len(x); {BUILTIN_HINT}",
    "size": f"use len(x); {BUILTIN_HINT}",
    "append": f"use push(xs, v); {BUILTIN_HINT}",
    "toString": f"use str(x); {BUILTIN_HINT}",
    "parseInt": f"use int(x); {BUILTIN_HINT}",
    "floor": "for integer division use int(a / b), which truncates toward zero",
    "range": "use a C-style loop: for (let i = 0; i < n; i++) { ... }",
    "in": "use a C-style loop: for (let i = 0; i < len(xs); i++) { ... }",
    "of": "use a C-style loop: for (let i = 0; i < len(xs); i++) { ... }",
}


def did_you_mean(name: str, candidates: Iterable[str]) -> str | None:
    if name in FOREIGN_NAMES:
        return FOREIGN_NAMES[name]
    matches = difflib.get_close_matches(name, list(candidates), n=1, cutoff=0.7)
    return f"did you mean '{matches[0]}'?" if matches else None


def syntax_hint(previous: str | None, found: str, expected: str | None) -> str | None:
    """Hint for a syntax error from the previous token, the unexpected one and the expected one."""
    if found == ".":
        if previous == "console":
            return "print a value with print(x)"
        return f"MiniLang has no methods or properties; {BUILTIN_HINT}"
    if found == "?":
        return "MiniLang has no ternary operator; use if / else"
    if found == "=" and previous in ("%",):
        return "MiniLang has no %= operator; write x = x % n"
    if previous in FOREIGN_NAMES and previous not in ("in", "of"):
        return FOREIGN_NAMES[previous]
    if found in ("in", "of") or (previous == "for" and expected == "'('"):
        return "use a C-style loop: for (let i = 0; i < len(xs); i++) { ... }"
    if previous in ("if", "while") and expected == "'('":
        return f"the condition needs parentheses: {previous} (condition) {{ ... }}"
    if expected == "'{'":
        return "function bodies need braces: fn name(a) { ... }"
    return None


FLOAT_ASSIGN_HINT = (
    "'/' always produces a float; for integer division use int(a / b), "
    "or start the variable as a float (e.g. 0.0)"
)
STRING_CONCAT_HINT = 'convert numbers to text with str(n): "Total: " + str(n)'
IMMUTABLE_STRING_HINT = "build a new string with + instead"
NEGATIVE_INDEX_HINT = "MiniLang has no negative indexes; use xs[len(xs) - 1] for the last item"
