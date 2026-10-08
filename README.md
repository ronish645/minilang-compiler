# MiniLang Compiler

[![CI](https://github.com/ronish645/minilang-compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/ronish645/minilang-compiler/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)
![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)
![Dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen)

A compiler for **MiniLang**, a small C/JavaScript-style language, written from scratch in Python with no parser generators and no runtime dependencies. It's also an **LLM benchmark**: since no model has seen MiniLang before, it measures whether Claude, GPT and open models can learn a new language from its spec and fix their own code using compiler feedback.

```
source ─▶ Lexer ─▶ Parser ─▶ Semantic Analyzer ─┬─▶ Code Generator  (three-address code + pseudo-assembly)
          tokens    AST       scopes + types     └─▶ Interpreter     (runs it, with resource limits)
```

```js
fn fib(n) {
    if (n < 2) { return n; }
    return fib(n - 1) + fib(n - 2);
}

for (let i = 0; i < 10; i++) {
    if (fib(i) % 2 == 0) {
        print(fib(i));
    }
}
```

## Quick start

```bash
git clone https://github.com/ronish645/minilang-compiler.git
cd minilang-compiler
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

minilang run examples/primes.ml          # execute a program
minilang check examples/primes.ml        # type-check without running
minilang compile examples/sample.ml --emit tac asm   # show intermediate code
echo 'print("hi");' | minilang run -     # read from stdin
minilang run examples/primes.ml --json   # machine-readable result
```

Exit codes: `0` success, `1` compile error, `2` usage error, `3` runtime error.

## Error messages

Every error names its stage and points at the exact source position:

```
$ minilang run examples/errors.ml
error[semantic]: variable 'sise' used before declaration
 --> examples/errors.ml:6:7
  |
6 | print(sise);
  |       ^
```

A missing `;` is reported right after the previous token instead of on the next line. With `--json`, the same error is returned as `{"stage", "message", "line", "col"}` for tools to consume.

## What each stage does

| Stage | Module | Responsibility |
|---|---|---|
| Lexer | [`lexer.py`](minilang/lexer.py) | Characters → tokens with line/column; maximal-munch operators, string escapes, comments |
| Parser | [`parser.py`](minilang/parser.py) | Recursive descent → AST; one method per grammar rule, precedence encoded in the call chain |
| Semantic analysis | [`semantic.py`](minilang/semantic.py) | Nested scopes and a symbol table; catches undeclared or duplicate names, `const` misuse, arity and type errors, using gradual typing for parameters |
| Code generation | [`codegen.py`](minilang/codegen.py) | Three-address code (temporaries, labels, conditional jumps) and stack-style pseudo-assembly |
| Interpreter | [`runtime.py`](minilang/runtime.py), [`values.py`](minilang/values.py) | Tree-walking execution with environments and closures; step, call-depth and output limits |
| Diagnostics | [`errors.py`](minilang/errors.py), [`diagnostics.py`](minilang/diagnostics.py) | Positioned error hierarchy; source-snippet rendering |
| API / CLI | [`pipeline.py`](minilang/pipeline.py), [`cli.py`](minilang/cli.py) | `compile_source`, non-raising `run_source`, and the `minilang` command |

The full language is defined in [docs/LANGUAGE_SPEC.md](docs/LANGUAGE_SPEC.md).

## Example: three-address code

`minilang compile examples/sample.ml --emit tac` lowers control flow into labels and jumps:

```
func add(a, b)
t1 = a + b
return t1
endfunc add
x = 10
y = 20
param x
param y
t2 = call add, 2
total = t2
print total
t3 = total > 20
if_false t3 goto ELSE1
print 'greater than twenty'
goto ENDIF2
label ELSE1
print 'small value'
label ENDIF2
```

## LLM benchmark

[`bench/`](bench/) runs models in an agent loop: they get the [language spec](docs/LANGUAGE_SPEC.md) and a task, call the compiler as a tool (`run_minilang`), and submit a program, which is graded by exact output. Four conditions vary only what the compiler says when code fails, from nothing (`oneshot`) to a one-line "failed" (`opaque`) to the full positioned diagnostic. Methodology and discussion: [bench/README.md](bench/README.md).

**Results** (640 episodes, 32 tasks, about $1.30 in API cost):

| Model | Pass rate | One-shot (can't run code) | Tested before submitting | Cost per solve |
|---|---|---|---|---|
| Claude Haiku 5.5 | **100%** | 32/32 | 97% | $0.0005 |
| GPT-6 Luna | **100%** | 32/32 | 100% | $0.0002 |
| GPT-6.1 Sol | **100%** | 32/32 | 100% | $0.0025 |
| Claude Sonnet 5.5 | 98% | 32/32 | 35% | $0.0070 |
| Qwen 2.5 3B (local) | 32% | 9/32 | 73% | free |

- Frontier models learned the language from the spec alone, including tasks designed around its differences from JavaScript and Python.
- Error-message quality had **no measurable effect**. Frontier models fixed every failure even with "the program failed", and the 3B model rarely fixed anything with any feedback.
- Every frontier-model failure was an **untested submission**.

The harness supports the Anthropic Messages API, the OpenAI Responses API and local models through Ollama, behind one adapter interface, with prompt caching, a resumable episode cache and a dry-run cost estimate.

## MCP server

`minilang-mcp` exposes the compiler to AI assistants over the [Model Context Protocol](https://modelcontextprotocol.io): `run_program`, `check_program` and `compile_program` tools, plus the spec as the `minilang://spec` resource.

```bash
pip install -e ".[mcp]"
minilang-mcp            # stdio server; register this command in Claude Desktop / Claude Code
```

## Design decisions

- **Gradual typing.** Literal and variable types are checked before running. Function parameters are typed `unknown` and checked at run time, so `fn isEven(n) { return n % 2 == 0; }` type-checks without type annotations.
- **No Python leaks.** Python treats `True == 1` and prints `None`. MiniLang's value layer ([`values.py`](minilang/values.py)) gives `true == 1` → `false` and prints `null`.
- **Safe by default.** The interpreter stops infinite loops, runaway recursion and output floods with a clean error. This is required before running code an LLM wrote.
- **Errors as data.** `run_source()` returns a `RunResult` instead of raising, which is the shape the CLI, an agent tool or an API endpoint wants.

## Testing

```bash
pytest --cov          # 300+ tests, 97% coverage
ruff check . && ruff format --check .
```

- **Golden tests** pin the tokens, AST, TAC, assembly and output of the programs in `tests/programs/`. They were captured from the original compiler before refactoring, to prove the refactor changed nothing.
- **Regression tests** cover 8 bugs found in the original version ([`test_regressions.py`](tests/test_regressions.py)).
- **Unit tests** cover each stage. **Docs tests** run every code example in this README and the spec.
- CI runs on Python 3.10–3.13.

## Roadmap

- [x] Package refactor, positioned errors, CLI, runtime limits, CI
- [x] Multi-provider LLM benchmark with feedback-quality experiment
- [x] MCP server exposing the compiler as tools for AI assistants
- [ ] Benchmark mid-size open models (7–14B), where error quality is most likely to matter
- [ ] Web playground showing every compiler stage

## Repository layout

```
minilang/        compiler package (one module per stage) + MCP server
bench/           LLM benchmark: tasks, agent loop, provider adapters, runner, report
tests/           unit, golden, regression, CLI, docs, MCP and benchmark tests
examples/        sample programs
docs/            language specification and build notes
```

Originally built for CS 453 (Compiler Design) at San Francisco Bay University, then rebuilt as a tested, packaged tool.
