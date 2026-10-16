# MiniLang: a compiler and LLM benchmark

[![CI](https://github.com/ronish645/minilang-compiler/actions/workflows/ci.yml/badge.svg)](https://github.com/ronish645/minilang-compiler/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%E2%80%933.13-blue)
![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)
![Dependencies](https://img.shields.io/badge/runtime%20dependencies-0-brightgreen)

**Can a language model learn a programming language it has never seen, from the spec alone? And when its code fails, how much do better compiler error messages help it recover?**

**[Live demo →](https://ronish645.github.io/minilang-compiler/)** run the compiler in your browser, explore the benchmark charts, and inspect every graded episode. **[REST API →](https://minilang-api.onrender.com/docs)** call the compiler over HTTP (the free host sleeps when idle, so the first request can take about a minute).

MiniLang is a small C/JavaScript-style language created for this project, so it can't be in any model's training data. This repo contains:

- **The compiler**, written from scratch in Python with no parser generators and no runtime dependencies: lexer, recursive-descent parser, gradual type checker, three-address code generator and a sandboxed interpreter with resource limits.
- **The benchmark** ([`bench/`](bench/README.md)): Claude, GPT and a local Qwen model learn MiniLang from its spec and write programs through a compiler-as-tool agent loop, under feedback conditions ranging from "the program failed" to fix-it hints.
- **An MCP server** that gives AI assistants the compiler as tools.

```
source ─▶ Lexer ─▶ Parser ─▶ Semantic Analyzer ─┬─▶ Code Generator  (three-address code + pseudo-assembly)
          tokens    AST       scopes + types     └─▶ Interpreter     (runs it, with resource limits)
```

```js
fn search(xs, target) {                 // binary search
    let lo = 0;
    let hi = len(xs) - 1;
    while (lo <= hi) {
        let mid = int((lo + hi) / 2);   // '/' always gives a float; int() truncates
        if (xs[mid] == target) { return mid; }
        if (xs[mid] < target) { lo = mid + 1; } else { hi = mid - 1; }
    }
    return -1;
}

let primes = [2, 3, 5, 7, 11, 13];
print("index of 7: " + str(search(primes, 7)));
```

**The language (v2.1):** ints, floats, strings, booleans, `null` and arrays; `let`/`const`; `if`, `while`, C-style `for`, `break`/`continue`; first-class functions with recursion, mutual recursion and closures (`makeAdder(5)(10)`, `fs[i](x)`); built-ins `len`, `push`, `pop`, `str`, `int`, `abs`, `min`, `max`, `ord`, `chr`, `slice`; short-circuit `&&`/`||`; gradual static typing with type joins across `if`/`else` branches. Full reference: [docs/LANGUAGE_SPEC.md](docs/LANGUAGE_SPEC.md).

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

Every error names its stage, points at the exact source position, and, where the compiler recognizes the mistake, suggests a fix:

```
$ minilang run examples/errors.ml
error[semantic]: variable 'sise' used before declaration
 --> examples/errors.ml:6:7
  |
6 | print(sise);
  |       ^
  = help: did you mean 'size'?
```

- **Fix-it hints** for habits carried over from other languages: `xs.length` (no methods), `var`, `True`/`None`, ternaries, `for x in xs`, `"n=" + n` (use `str(n)`), `n = n / 2` on an int (use `int()`).
- **Every independent error in one run.** The semantic analyzer keeps going after an error, and the parser skips just the broken statement (tracking brackets), so one mistake gives one error, not a cascade.
- A missing `;` is reported right after the previous token instead of on the next line.
- With `--json`, errors come back as `{"stage", "message", "line", "col", "hint", "additional"}` for tools to consume.

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

## REST API

A FastAPI service for calling the compiler over HTTP ([`minilang/api/`](minilang/api/)), live at **https://minilang-api.onrender.com** with interactive docs at [`/docs`](https://minilang-api.onrender.com/docs). It runs on Render's free tier, which sleeps after 15 idle minutes, so the first request after that takes up to a minute.

| Endpoint | Does |
|---|---|
| `POST /v1/run` | Compile and run; output, every error with fix-it hints, and the diagnostic |
| `POST /v1/check` | Type-check without running |
| `POST /v1/compile` | Every stage: tokens, AST, three-address code, pseudo-assembly, output |
| `GET /v1/spec` | The language spec (Markdown), e.g. for an AI agent learning MiniLang |
| `GET /health` | Liveness check |

```bash
pip install -e ".[api]"
uvicorn minilang.api.app:app --reload        # http://127.0.0.1:8000/docs

curl -s -X POST localhost:8000/v1/run -H 'Content-Type: application/json' \
  -d '{"source": "let xs = [1, 2];\nprint(xs.length);"}'
# {"ok": false, "errors": [{"stage": "syntax", "message": "expected ')' but found '.'",
#   "line": 2, "col": 9, "hint": "MiniLang has no methods or properties; built-ins are len(x), ..."}], ...}
```

- **Program errors are data:** a syntax, type or runtime error in the program is a `200` with `ok: false`. Request problems are `4xx` with `{"error": {"code", "message", "details"}}`; `500` and `503` use the same shape, and every response (errors included) carries `X-Request-ID` and the CORS headers.
- **Limits:** 30 requests per minute per client on the compiler endpoints (token bucket; `429` with `Retry-After`, checked before the body is read), request bodies capped whether sent with `Content-Length` or chunked (`413`), programs up to 20,000 characters (a setting can lower this), at most 4 programs compiling at once (`503 server_busy` with `Retry-After: 1`), and the interpreter's step, call-depth and output limits.
- **Client IP behind a proxy:** `X-Forwarded-For` is not trusted blindly. `MINILANG_CLIENT_IP_HEADER` names a header the edge proxy overwrites with the client IP (`CF-Connecting-IP` on Render, which sits behind Cloudflare); `MINILANG_TRUSTED_PROXY_HOPS=N` instead takes the N-th `X-Forwarded-For` entry from the right; the default uses the socket peer. Run uvicorn with `--no-proxy-headers` so it doesn't rewrite the address first (the Dockerfile does).
- **Deploy:** `docker build -t minilang-api . && docker run -p 8000:8000 minilang-api`, or the Render blueprint in [`render.yaml`](render.yaml) (which sets one trusted proxy hop). Settings come from `MINILANG_*` environment variables ([`config.py`](minilang/api/config.py)).

## Design decisions

- **Gradual typing.** Literal and variable types are checked before running. Function parameters are typed `unknown` and checked at run time, so `fn isEven(n) { return n % 2 == 0; }` type-checks without type annotations.
- **No Python leaks.** Python treats `True == 1` and prints `None`. MiniLang's value layer ([`values.py`](minilang/values.py)) gives `true == 1` → `false` and prints `null`.
- **Safe by default.** The interpreter stops infinite loops, runaway recursion and output floods with a clean error. This is required before running code an LLM wrote.
- **Errors as data.** `run_source()` returns a `RunResult` instead of raising, which is the shape the CLI, an agent tool or an API endpoint wants.

## Testing

```bash
pytest --cov          # 530+ tests, 98% coverage
ruff check . && ruff format --check .
```

- **Golden tests** pin the tokens, AST, TAC, assembly and output of the programs in `tests/programs/`. They were captured from the original compiler before refactoring, to prove the refactor changed nothing.
- **Regression tests** cover 8 bugs found in the original version ([`test_regressions.py`](tests/test_regressions.py)).
- **Unit tests** cover each stage. **Docs tests** run every code example in this README and the spec.
- CI runs on Python 3.10–3.13, builds the API's Docker image and calls it.

## Roadmap

- [x] Package refactor, positioned errors, CLI, runtime limits, CI
- [x] Multi-provider LLM benchmark with feedback-quality experiment
- [x] MCP server exposing the compiler as tools for AI assistants
- [x] REST API (FastAPI): run/check/compile endpoints, rate limiting, Docker, Render deploy
- [x] Showcase site: in-browser playground (Pyodide), benchmark charts, episode explorer
- [x] v2.1: calls on any expression (first-class functions), `if`/`else` type joins, `abs`/`min`/`max`/`ord`/`chr`/`slice`
- [ ] Benchmark mid-size open models (7–14B), where error quality is most likely to matter
- [ ] Typed AST (one dataclass per node kind) instead of positional `children[i]`
- [ ] A small VM that executes the generated TAC, checked against the interpreter on every test program
- [ ] Interactive REPL

## Repository layout

```
minilang/        compiler package (one module per stage), MCP server, REST API (api/)
bench/           LLM benchmark: tasks, agent loop, provider adapters, runner, report
tests/           unit, golden, regression, CLI, docs, MCP and benchmark tests
examples/        sample programs
docs/            language specification and build notes
site/            showcase website (React + Tailwind; the compiler runs in the browser via Pyodide)
```

Originally built for CS 453 (Compiler Design) at San Francisco Bay University, then rebuilt as a tested, packaged tool.
