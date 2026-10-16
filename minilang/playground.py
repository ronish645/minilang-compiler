"""Every compiler stage as JSON-ready data, for interactive front ends.

``compile_source`` returns pretty-printed strings and stops at the first
failure. A UI wants structure instead (a token table, an AST it can draw as a
tree, error positions it can underline) and wants to keep every stage that
succeeded before the failure. ``explore`` provides that. The showcase site
calls it in the browser through Pyodide.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

from minilang.ast_nodes import ASTNode
from minilang.codegen import CodeGenerator
from minilang.diagnostics import format_diagnostic
from minilang.errors import MiniLangError, MiniLangRuntimeError
from minilang.lexer import Lexer
from minilang.parser import Parser
from minilang.recursion import FRONT_END_RECURSION_LIMIT, python_recursion_limit
from minilang.runtime import MiniRuntime, RuntimeLimits
from minilang.semantic import SemanticAnalyzer

# Browsers run Python more slowly, so stop runaway programs sooner than the CLI does.
PLAYGROUND_LIMITS = RuntimeLimits(
    max_steps=200_000,
    max_output_lines=2_000,
    max_output_chars=100_000,
    max_string_length=100_000,
    max_array_length=100_000,
    max_alloc_units=50_000_000,  # ~50 MB of strings and array slots per run
    max_seconds=2.0,
)

T = TypeVar("T")


def ast_to_dict(node: ASTNode) -> dict[str, Any]:
    return {
        "kind": node.kind,
        "value": node.value,
        "type": node.literal_type,
        "line": node.line,
        "col": node.col,
        "children": [ast_to_dict(child) for child in node.children],  # depth <= MAX_TREE_DEPTH
    }


def error_list(error: MiniLangError) -> list[dict[str, Any]]:
    """The first error and every additional one, without nesting."""
    return [
        {"stage": e.stage, "message": e.message, "line": e.line, "col": e.col, "hint": e.hint}
        for e in (error, *error.additional)
    ]


def timed(timings: dict[str, float], stage: str, work: Callable[[], T]) -> T:
    start = time.perf_counter()
    try:
        return work()
    finally:
        timings[stage] = round((time.perf_counter() - start) * 1000, 3)


def explore(source: str, limits: RuntimeLimits = PLAYGROUND_LIMITS) -> dict[str, Any]:
    """Run each stage in order, keeping everything produced before a failure."""
    result: dict[str, Any] = {
        "ok": False,
        "failed_stage": None,
        "tokens": None,
        "ast": None,
        "tac": None,
        "asm": None,
        "output": [],
        "errors": [],
        "diagnostic": None,
        "timings_ms": {},
    }
    timings = result["timings_ms"]
    try:
        tokens = timed(timings, "lex", Lexer(source).tokenize)
        result["tokens"] = [
            {"type": t.type, "value": t.value, "line": t.line, "col": t.col} for t in tokens
        ]
        ast = timed(timings, "parse", Parser(tokens).parse)
        with python_recursion_limit(FRONT_END_RECURSION_LIMIT):
            result["ast"] = ast_to_dict(ast)
        timed(timings, "check", lambda: SemanticAnalyzer().analyze(ast))
        result["tac"], result["asm"] = timed(
            timings, "codegen", lambda: CodeGenerator().generate(ast)
        )
        result["output"] = timed(timings, "run", lambda: MiniRuntime(limits).run(ast))
        result["ok"] = True
    except MiniLangError as error:
        result["failed_stage"] = error.stage
        result["errors"] = error_list(error)
        result["diagnostic"] = format_diagnostic(error, source, "playground.ml")
        if isinstance(error, MiniLangRuntimeError):
            result["output"] = error.partial_output
    return result
