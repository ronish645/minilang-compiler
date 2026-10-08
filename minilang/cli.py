"""Command-line interface for the MiniLang compiler."""

from __future__ import annotations

import argparse
import json
from typing import Any

from minilang.errors import MiniLangError
from minilang.pipeline import compile_source

SAMPLE_PROGRAM = r"""
fn add(a, b) {
    return a + b;
}

let x = 10;
let y = 20;
let total = add(x, y);
print(total);

if (total > 20) {
    print("greater than twenty");
} else {
    print("small value");
}

for (let i = 0; i < 3; i++) {
    print(i);
}
"""


def format_report(result: dict[str, Any]) -> str:
    sections = [
        ("1. TOKENS", "\n".join(result["tokens"])),
        ("2. LEXICAL TABLE", json.dumps(result["lexical_table"], indent=2)),
        ("3. AST", result["ast"]),
        ("4. SEMANTIC ANALYSIS", "Semantic analysis successful"),
        ("5. THREE-ADDRESS CODE", "\n".join(result["three_address_code"])),
        ("6. PSEUDO CODE", "\n".join(result["pseudo_code"])),
        ("7. EXECUTION OUTPUT", "\n".join(result["execution_output"])),
    ]
    parts = ["MINILANG COMPILER\n", "=" * 60]
    for title, body in sections:
        parts += [f"\n{title}\n", body]
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description="MiniLang compiler")
    parser.add_argument("source", nargs="?", help="MiniLang source file")
    parser.add_argument("--demo", action="store_true", help="Run built-in demo program")
    parser.add_argument("--json", action="store_true", help="Print JSON output")
    args = parser.parse_args()

    if args.demo or not args.source:
        source = SAMPLE_PROGRAM
    else:
        with open(args.source, encoding="utf-8") as f:
            source = f.read()

    try:
        result = compile_source(source)
        print(json.dumps(result, indent=2) if args.json else format_report(result))
    except MiniLangError as e:
        print(f"ERROR: {e}")


if __name__ == "__main__":
    main()
