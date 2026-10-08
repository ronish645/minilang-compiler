"""Public API: run the compiler pipeline on MiniLang source code.

    source -> Lexer -> tokens -> Parser -> AST -> SemanticAnalyzer
           -> CodeGenerator (TAC + pseudo-asm)
           -> MiniRuntime (program output)

``compile_source`` raises ``MiniLangError`` on failure and is meant for
callers that want every intermediate stage. ``run_source`` never raises for
problems in the program; it returns a ``RunResult``, which is the shape tools
(the CLI, the LLM agent, the MCP server) want.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from minilang.ast_nodes import ASTNode
from minilang.codegen import CodeGenerator
from minilang.diagnostics import format_diagnostic
from minilang.errors import MiniLangError, MiniLangRuntimeError
from minilang.lexer import Lexer, Token
from minilang.parser import Parser
from minilang.runtime import MiniRuntime, RuntimeLimits
from minilang.semantic import SemanticAnalyzer


def analyze_source(source: str) -> tuple[Lexer, list[Token], ASTNode]:
    """Front end: lex, parse and type-check. Returns (lexer, tokens, ast)."""
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    ast = Parser(tokens).parse()
    SemanticAnalyzer().analyze(ast)
    return lexer, tokens, ast


def compile_source(
    source: str, *, execute: bool = True, limits: RuntimeLimits | None = None
) -> dict[str, Any]:
    """Run every stage and return all intermediate representations."""
    lexer, tokens, ast = analyze_source(source)
    tac, pseudo = CodeGenerator().generate(ast)
    result: dict[str, Any] = {
        "tokens": [repr(t) for t in tokens],
        "lexical_table": lexer.lexical_table(),
        "ast": ast.pretty(),
        "three_address_code": tac,
        "pseudo_code": pseudo,
    }
    if execute:
        result["execution_output"] = MiniRuntime(limits).run(ast)
    return result


@dataclass(frozen=True)
class RunResult:
    ok: bool
    output: list[str] = field(default_factory=list)
    error: dict[str, Any] | None = None  # MiniLangError.to_dict()
    diagnostic: str | None = None  # human-readable error with source snippet

    @property
    def is_compile_error(self) -> bool:
        return self.error is not None and self.error["stage"] != "runtime"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_source(
    source: str, *, filename: str = "<input>", limits: RuntimeLimits | None = None
) -> RunResult:
    """Compile and execute; report failures as data instead of raising."""
    try:
        _, _, ast = analyze_source(source)
        return RunResult(ok=True, output=MiniRuntime(limits).run(ast))
    except MiniLangError as error:
        partial = error.partial_output if isinstance(error, MiniLangRuntimeError) else []
        return RunResult(
            ok=False,
            output=partial,
            error=error.to_dict(),
            diagnostic=format_diagnostic(error, source, filename),
        )
