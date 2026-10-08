"""Runs the full compiler pipeline: source -> tokens -> AST -> checks -> TAC -> output."""

from __future__ import annotations

from typing import Any

from minilang.codegen import CodeGenerator
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.runtime import MiniRuntime
from minilang.semantic import SemanticAnalyzer


def compile_source(source: str) -> dict[str, Any]:
    lexer = Lexer(source)
    tokens = lexer.tokenize()

    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    tac, pseudo = CodeGenerator().generate(ast)
    output = MiniRuntime().run(ast)

    return {
        "tokens": [repr(t) for t in tokens],
        "lexical_table": lexer.lexical_table(),
        "ast": ast.pretty(),
        "three_address_code": tac,
        "pseudo_code": pseudo,
        "execution_output": output,
    }
