"""Command-line interface.

    minilang run FILE        execute a program, print its output
    minilang check FILE      lex + parse + type-check only
    minilang compile FILE    show intermediate stages (tokens, AST, TAC, asm)
    minilang demo            compile and run a built-in sample

FILE may be ``-`` to read from stdin. Add ``--json`` for machine-readable output.

Exit codes: 0 success, 1 compile error, 2 usage error (argparse's convention),
3 runtime error.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from minilang.diagnostics import format_diagnostic
from minilang.errors import MiniLangError
from minilang.pipeline import analyze_source, compile_source, run_source

EXIT_OK = 0
EXIT_COMPILE_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_RUNTIME_ERROR = 3

STAGES = {
    "tokens": "TOKENS",
    "ast": "AST",
    "tac": "THREE-ADDRESS CODE",
    "asm": "PSEUDO-ASSEMBLY",
}
STAGE_RESULT_KEYS = {
    "tokens": "tokens",
    "ast": "ast",
    "tac": "three_address_code",
    "asm": "pseudo_code",
}

SAMPLE_PROGRAM = """\
fn add(a, b) {
    return a + b;
}

let total = add(10, 20);
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


def read_source(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8") as f:
        return f.read()


def print_json(data: dict[str, Any]) -> None:
    print(json.dumps(data, indent=2))


def cmd_run(source: str, filename: str, as_json: bool) -> int:
    result = run_source(source, filename=filename)
    if as_json:
        print_json(result.to_dict())
    else:
        for line in result.output:
            print(line)
        if result.diagnostic:
            print(result.diagnostic, file=sys.stderr)
    if result.ok:
        return EXIT_OK
    return EXIT_COMPILE_ERROR if result.is_compile_error else EXIT_RUNTIME_ERROR


def cmd_check(source: str, filename: str, as_json: bool) -> int:
    try:
        analyze_source(source)
    except MiniLangError as error:
        if as_json:
            print_json({"ok": False, "error": error.to_dict()})
        else:
            print(format_diagnostic(error, source, filename), file=sys.stderr)
        return EXIT_COMPILE_ERROR
    if as_json:
        print_json({"ok": True, "error": None})
    else:
        print(f"{filename}: ok")
    return EXIT_OK


def cmd_compile(source: str, filename: str, as_json: bool, stages: list[str]) -> int:
    try:
        result = compile_source(source, execute=False)
    except MiniLangError as error:
        if as_json:
            print_json({"ok": False, "error": error.to_dict()})
        else:
            print(format_diagnostic(error, source, filename), file=sys.stderr)
        return EXIT_COMPILE_ERROR

    selected = {stage: result[STAGE_RESULT_KEYS[stage]] for stage in stages}
    if as_json:
        print_json({"ok": True, **selected})
        return EXIT_OK
    for stage, value in selected.items():
        body = value if isinstance(value, str) else "\n".join(value)
        print(f"== {STAGES[stage]} ==\n{body.rstrip()}\n")
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="minilang", description="The MiniLang compiler")
    commands = parser.add_subparsers(dest="command", required=True)

    def add_command(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text)
        if name != "demo":
            sub.add_argument("file", help="source file, or - for stdin")
        sub.add_argument("--json", action="store_true", help="machine-readable output")
        return sub

    add_command("run", "execute a program")
    add_command("check", "lex, parse and type-check without running")
    compile_cmd = add_command("compile", "show intermediate representations")
    compile_cmd.add_argument(
        "--emit",
        nargs="+",
        choices=list(STAGES),
        default=list(STAGES),
        help="which stages to show (default: all)",
    )
    add_command("demo", "compile and run a built-in sample program")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "demo":
        print(f"== SOURCE ==\n{SAMPLE_PROGRAM}")
        cmd_compile(SAMPLE_PROGRAM, "<demo>", args.json, list(STAGES))
        print("== OUTPUT ==")
        return cmd_run(SAMPLE_PROGRAM, "<demo>", args.json)

    filename = "<stdin>" if args.file == "-" else args.file
    try:
        source = read_source(args.file)
    except OSError as error:
        print(f"minilang: cannot read {filename}: {error.strerror}", file=sys.stderr)
        return EXIT_USAGE_ERROR

    if args.command == "run":
        return cmd_run(source, filename, args.json)
    if args.command == "check":
        return cmd_check(source, filename, args.json)
    return cmd_compile(source, filename, args.json, args.emit)


if __name__ == "__main__":
    sys.exit(main())
