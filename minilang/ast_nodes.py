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

    def pretty(self, level: int = 0) -> str:
        indent = "  " * level
        s = f"{indent}{self.kind}"
        if self.value is not None:
            s += f": {self.value}"
        s += "\n"
        for child in self.children:
            s += child.pretty(level + 1)
        return s
