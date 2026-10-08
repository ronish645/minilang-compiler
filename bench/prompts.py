"""Prompts and tool definitions given to the model."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bench.llm.base import ToolSpec

SPEC_FILE = Path(__file__).parent.parent / "docs" / "LANGUAGE_SPEC.md"

RUN_TOOL = "run_minilang"
SUBMIT_TOOL = "submit_solution"
CODE_SCHEMA = {
    "type": "object",
    "properties": {"code": {"type": "string", "description": "A complete MiniLang program"}},
    "required": ["code"],
    "additionalProperties": False,
}
TOOLS = [
    ToolSpec(
        RUN_TOOL,
        "Compile and run a MiniLang program. Returns its printed output, or an error.",
        CODE_SCHEMA,
    ),
    ToolSpec(
        SUBMIT_TOOL,
        "Submit your final MiniLang program for grading. Call this exactly once, when "
        "you are confident it prints exactly the expected output. This ends the task.",
        CODE_SCHEMA,
    ),
]

INTRO = (
    "You write programs in MiniLang, a small programming language you have not seen "
    "before. Its complete specification is below. MiniLang differs from JavaScript and "
    "Python in several ways, so rely on the specification, not on habits from other "
    "languages."
)

TOOL_INSTRUCTIONS = (
    "Use the {run} tool to test your program. You may run code at most {max_runs} times. "
    "When the output matches the expected output exactly, call {submit} with the final "
    "program."
)

ONESHOT_INSTRUCTIONS = (
    "You cannot run code. Reply with the complete program in a single fenced code "
    "block (```minilang ... ```)."
)


def load_spec() -> str:
    return SPEC_FILE.read_text()


def system_prompt(spec: str, uses_tools: bool, max_runs: int) -> str:
    instructions = (
        TOOL_INSTRUCTIONS.format(run=RUN_TOOL, submit=SUBMIT_TOOL, max_runs=max_runs)
        if uses_tools
        else ONESHOT_INSTRUCTIONS
    )
    return f"{INTRO}\n\n<specification>\n{spec}\n</specification>\n\n{instructions}"


def fingerprint(*parts: str) -> str:
    """Short stable hash, used to invalidate cached results when prompts change."""
    digest = hashlib.sha256("\x00".join(parts).encode()).hexdigest()
    return digest[:12]
