"""MCP server exposing the MiniLang compiler as tools for AI assistants.

    pip install -e ".[mcp]"
    minilang-mcp                # serves over stdio

Register it in an MCP client (Claude Desktop, Claude Code, ...) as a stdio
server running ``minilang-mcp``. The assistant can then read the language
spec resource, write MiniLang, and run or check it with these tools.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from minilang.codegen import CodeGenerator
from minilang.diagnostics import format_diagnostic
from minilang.errors import MiniLangError
from minilang.pipeline import analyze_source, run_source

SPEC_PATH = Path(__file__).parent.parent / "docs" / "LANGUAGE_SPEC.md"
MAX_SOURCE_CHARS = 100_000  # reject absurdly large inputs before compiling
# Every tool is a pure function of its input: safe to call and to repeat.
PURE = ToolAnnotations(readOnlyHint=True, idempotentHint=True, openWorldHint=False)

server = MCPServer(
    "minilang",
    instructions=(
        "Tools for the MiniLang programming language. Read the minilang://spec resource "
        "before writing MiniLang: it differs from JavaScript and Python (no break, '/' "
        "always returns a float, && does not short-circuit, no int-to-string conversion). "
        "Use check_program for fast feedback and run_program to execute."
    ),
)


def validate_source(code: str) -> str | None:
    if len(code) > MAX_SOURCE_CHARS:
        return f"program is too large ({len(code)} characters; limit {MAX_SOURCE_CHARS})"
    return None


def input_error(message: str) -> dict[str, Any]:
    return {"ok": False, "error": {"stage": "input", "message": message}, "diagnostic": None}


@server.tool(annotations=PURE)
def run_program(code: str) -> dict[str, Any]:
    """Compile and execute a MiniLang program.

    Returns ok, the printed output lines, and on failure a structured error
    (stage, message, line, col) plus a human-readable diagnostic.
    """
    if problem := validate_source(code):
        return input_error(problem)
    return run_source(code, filename="program.ml").to_dict()


@server.tool(annotations=PURE)
def check_program(code: str) -> dict[str, Any]:
    """Lex, parse and type-check a MiniLang program without running it."""
    if problem := validate_source(code):
        return input_error(problem)
    try:
        analyze_source(code)
    except MiniLangError as error:
        diagnostic = format_diagnostic(error, code, "program.ml")
        return {"ok": False, "error": error.to_dict(), "diagnostic": diagnostic}
    return {"ok": True, "error": None, "diagnostic": None}


@server.tool(annotations=PURE)
def compile_program(code: str) -> dict[str, Any]:
    """Show a MiniLang program's AST, three-address code and pseudo-assembly."""
    if problem := validate_source(code):
        return input_error(problem)
    try:
        _, _, ast = analyze_source(code)
    except MiniLangError as error:
        diagnostic = format_diagnostic(error, code, "program.ml")
        return {"ok": False, "error": error.to_dict(), "diagnostic": diagnostic}
    tac, pseudo = CodeGenerator().generate(ast)
    return {"ok": True, "ast": ast.pretty(), "three_address_code": tac, "pseudo_assembly": pseudo}


@server.resource(
    "minilang://spec",
    name="language-spec",
    description="The complete MiniLang language specification",
    mime_type="text/markdown",
)
def language_spec() -> str:
    return SPEC_PATH.read_text()


def main() -> None:
    server.run()  # stdio transport


if __name__ == "__main__":
    main()
