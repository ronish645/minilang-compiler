"""The abstract syntax tree (AST) produced by the parser.

MiniLang uses a single generic node type: ``kind`` names the construct
(``If``, ``BinaryOp``, ...), ``value`` holds a payload such as an operator or
identifier name, and ``children`` holds sub-trees in a fixed order per kind.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ASTNode:
    kind: str
    value: Any = None
    children: list[ASTNode] = field(default_factory=list)
    # Only set on Literal nodes: "int" | "float" | "string" | "bool" | "null".
    # Kept separately because ``value`` stores the raw source text, and the
    # string "42" must not be confused with the number 42.
    literal_type: str | None = None
    # Source position of the token that starts this construct (0 = unknown).
    line: int = 0
    col: int = 0

    def pretty(self, level: int = 0) -> str:
        indent = "  " * level
        s = f"{indent}{self.kind}"
        if self.value is not None:
            s += f": {self.value}"
        s += "\n"
        for child in self.children:
            s += child.pretty(level + 1)
        return s
