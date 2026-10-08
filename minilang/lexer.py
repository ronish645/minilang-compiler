"""Lexer: turns source text into a flat list of tokens.

It scans one character at a time, tracking line/column so later stages can
report precise error locations.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from minilang.errors import LexerError


@dataclass(frozen=True)
class Token:
    type: str
    value: str
    line: int
    col: int

    def __repr__(self) -> str:
        return f"{self.type}({self.value!r})@{self.line}:{self.col}"


EOF_CHAR = "\0"
STRING_ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", "'": "'", '"': '"'}


class Lexer:
    KEYWORDS: frozenset[str] = frozenset(
        {
            "let",
            "const",
            "if",
            "else",
            "while",
            "for",
            "fn",
            "return",
            "print",
            "true",
            "false",
            "null",
        }
    )

    # Longest operators first so "==" wins over "=" (maximal munch).
    OPERATORS: tuple[str, ...] = (
        "++",
        "--",
        "->",
        "===",
        "==",
        "!=",
        "<=",
        ">=",
        "+=",
        "-=",
        "*=",
        "/=",
        "&&",
        "||",
        "=",
        "+",
        "-",
        "*",
        "/",
        "%",
        "<",
        ">",
        "!",
    )

    SEPARATORS: frozenset[str] = frozenset({"(", ")", "{", "}", "[", "]", ",", ";", ":", "."})
    LINE_COMMENT = "//"
    BLOCK_COMMENT_START = "/*"
    BLOCK_COMMENT_END = "*/"

    def __init__(self, source: str):
        self.source = source
        self.i = 0
        self.line = 1
        self.col = 1
        self.identifiers: set[str] = set()
        self.constants: set[str] = set()

    # ---- character helpers -------------------------------------------------
    def peek(self, k: int = 0) -> str:
        j = self.i + k
        return self.source[j] if j < len(self.source) else EOF_CHAR

    def advance(self) -> str:
        ch = self.peek()
        self.i += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def startswith(self, s: str) -> bool:
        return all(self.peek(k) == s[k] for k in range(len(s)))

    # ---- token scanners ----------------------------------------------------
    def lex_identifier_or_keyword(self) -> Token:
        line, col = self.line, self.col
        s = ""
        while self.peek().isalnum() or self.peek() == "_":
            s += self.advance()

        if s in self.KEYWORDS:
            return Token("KW", s, line, col)

        self.identifiers.add(s)
        return Token("IDENT", s, line, col)

    def lex_number(self) -> Token:
        line, col = self.line, self.col
        s = ""
        while self.peek().isdigit():
            s += self.advance()

        is_float = False
        if self.peek() == "." and self.peek(1).isdigit():
            is_float = True
            s += self.advance()
            while self.peek().isdigit():
                s += self.advance()

        if self.peek() in ("e", "E"):
            nxt, nxt2 = self.peek(1), self.peek(2)
            if nxt.isdigit() or (nxt in "+-" and nxt2.isdigit()):
                is_float = True
                s += self.advance()
                if self.peek() in "+-":
                    s += self.advance()
                while self.peek().isdigit():
                    s += self.advance()

        self.constants.add(s)
        return Token("FLOAT" if is_float else "INT", s, line, col)

    def lex_string(self) -> Token:
        quote = self.peek()
        line, col = self.line, self.col
        self.advance()
        out = ""

        while True:
            ch = self.peek()
            if ch == EOF_CHAR:
                raise LexerError(f"Unterminated string at {line}:{col}")
            if ch == quote:
                # SQL-style doubled single quote: 'it''s' -> it's
                if quote == "'" and self.peek(1) == "'":
                    self.advance()
                    self.advance()
                    out += "'"
                    continue
                self.advance()
                break
            if ch == "\\":
                self.advance()
                esc = self.peek()
                if esc in STRING_ESCAPES:
                    out += STRING_ESCAPES[esc]
                    self.advance()
                else:
                    out += "\\" + self.advance()
                continue
            out += self.advance()

        self.constants.add(out)
        return Token("STRING", out, line, col)

    def lex_operator(self) -> Token | None:
        line, col = self.line, self.col
        for op in self.OPERATORS:
            if self.startswith(op):
                for _ in range(len(op)):
                    self.advance()
                return Token("OP", op, line, col)
        return None

    def skip_comment_if_present(self) -> bool:
        if self.startswith(self.LINE_COMMENT):
            while self.peek() not in ("\n", EOF_CHAR):
                self.advance()
            return True

        if self.startswith(self.BLOCK_COMMENT_START):
            self.advance()
            self.advance()
            while True:
                if self.peek() == EOF_CHAR:
                    raise LexerError(f"Unterminated block comment at {self.line}:{self.col}")
                if self.startswith(self.BLOCK_COMMENT_END):
                    self.advance()
                    self.advance()
                    return True
                self.advance()
        return False

    # ---- main loop ---------------------------------------------------------
    def tokenize(self) -> list[Token]:
        tokens: list[Token] = []
        while self.peek() != EOF_CHAR:
            ch = self.peek()
            if ch.isspace():
                self.advance()
                continue
            if ch in ("'", '"'):
                tokens.append(self.lex_string())
                continue
            if self.skip_comment_if_present():
                continue
            if ch.isdigit():
                tokens.append(self.lex_number())
                continue
            if ch.isalpha() or ch == "_":
                tokens.append(self.lex_identifier_or_keyword())
                continue
            if ch in self.SEPARATORS:
                line, col = self.line, self.col
                tokens.append(Token("SEP", self.advance(), line, col))
                continue
            op = self.lex_operator()
            if op is not None:
                tokens.append(op)
                continue
            raise LexerError(f"Unexpected character {ch!r} at {self.line}:{self.col}")

        tokens.append(Token("EOF", "", self.line, self.col))
        return tokens

    def lexical_table(self) -> dict[str, Any]:
        return {
            "identifiers": sorted(self.identifiers),
            "constants": sorted(self.constants),
            "keywords": sorted(self.KEYWORDS),
            "operators": list(self.OPERATORS),
            "separators": sorted(self.SEPARATORS),
        }
