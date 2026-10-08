# MiniLang Upgrade: Build Notes

**Date:** 2026-10-08 · **Author:** Ronish Shrestha · **Repo:** [ronish645/minilang-compiler](https://github.com/ronish645/minilang-compiler)

These notes explain what we built, how each piece works, why each decision was made, and how to talk about it in an interview. With these notes and the repo, you should be able to rebuild the project from scratch.

---

## 1. Why this project, and why this upgrade

The original MiniLang compiler was a CS 453 course project: one 1,439-line Python file that lexed, parsed, type-checked, generated code and ran MiniLang programs. It showed compiler fundamentals but read like coursework: no tests, no packaging, errors without locations, and nothing connecting it to AI.

The upgrade had two goals, both aimed at Forward Deployed / Solutions / Applied AI roles:

1. **Make it production-grade** (Phase 1). Interviewers for these roles ask: *how do you know it works? Could a teammate maintain it?* Tests, CI, clean modules and good errors answer that.
2. **Use it to evaluate LLMs** (Phase 2). A language no model has ever seen is a good probe: can a model learn it from a spec and use compiler feedback to fix its mistakes? Answering that exercises the core skills of applied AI work: **tool calling, agent loops, integrating several providers' APIs, and running evals honestly.**

---

## 2. The big picture

```
                         ┌──────────────────────── minilang/ (the compiler) ─────────────────────────┐
source ─▶ lexer.py ─▶ parser.py ─▶ semantic.py ─┬─▶ codegen.py   (three-address code + pseudo-asm)
          tokens       AST          scopes,      └─▶ runtime.py   (interpreter + resource limits)
                                    types                values.py  (MiniLang value semantics)
          errors.py / diagnostics.py: every error has a stage, line, col, and a pretty snippet
          pipeline.py: compile_source() raises · run_source() returns a RunResult (errors as data)
          cli.py: `minilang run|check|compile|demo`   ·   mcp_server.py: tools for AI assistants
                         └───────────────────────────────────────────────────────────────────────────┘

                         ┌──────────────────────── bench/ (the LLM benchmark) ───────────────────────┐
tasks.yaml ─▶ runner.py ─▶ agent.py (tool loop) ─▶ llm/ adapters ─▶ Anthropic | OpenAI | Ollama
                              │  run_minilang / submit_solution
                              └─▶ minilang.run_source ─▶ feedback.py (4 conditions) ─▶ grading.py
                         report.py ─▶ pass rate, repair rate, Wilson CIs, cost per solve
                         └───────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Phase 1: making the compiler production-grade

### 3.1 Safety net first: golden (characterization) tests

**What:** before moving any code, we ran the *original* compiler on 5 programs and saved everything it produced (tokens, AST, three-address code, pseudo-assembly, program output) as JSON snapshots in `tests/golden/`. `tests/test_golden.py` checks that the new code produces exactly the same.

**Why:** a refactor should change structure, not behavior. With no existing tests, the only trustworthy definition of "correct" was "whatever the old code did". Recording that first turned the refactor from a risk into a mechanical check. Michael Feathers calls these **characterization tests**: they describe what the code *does*, not what it *should* do.

**Order mattered:** snapshot → refactor (snapshots still pass) → *then* fix bugs. Fixing bugs during the refactor would have made it impossible to tell an intended change from an accident.

### 3.2 Splitting the monolith into a package

One module per compiler stage, each under 330 lines. Two simplifications along the way:

- **Parser precedence levels share one helper.** Every binary-operator level (`||`, `&&`, `==`, `<`, `+`, `*`) had the same loop. `binary_left_assoc(ops, next_level)` replaced six copies:
  ```python
  def binary_left_assoc(self, ops, operand):
      node = operand()
      while self.check_op(ops):
          op = self.advance()
          node = make_node("BinaryOp", op, value=op.value, children=[node, operand()])
      return node
  ```
  Each precedence level is now one line, e.g. `term = binary_left_assoc(("+", "-"), self.factor)`. Lower-precedence rules call higher ones, so `*` binds tighter than `+`.
- **The interpreter uses visitor dispatch** (`exec_If`, `eval_BinaryOp`, ... looked up with `getattr`) instead of a 60-line `if kind == ...` chain. This matches the semantic analyzer and code generator.

### 3.3 The 8 bugs (each fixed test-first)

| # | Symptom | Root cause | Fix |
|---|---|---|---|
| 1 | `fn isEven(n) { return n % 2 == 0; }` → "cannot compare unknown with int" | Parameters have type `unknown`, and `unknown` was compatible with nothing | **Gradual typing:** `unknown` is accepted wherever a concrete type is; real mismatches are caught at run time |
| 2 | `if (isEven(4))` → "condition must be boolean" | Call results are `unknown` too | Same fix |
| 3 | The string `"42"` was treated as the int 42 | The parser stored only the literal's *text* and later stages guessed its type from it | AST `Literal` nodes keep a `literal_type` from the token |
| 4 | The string `"true"` was a boolean | Same root cause | Same fix |
| 5 | `print(true)` showed `True`; `null` showed `None` | Python's `str()` leaked through | `values.format_value()` prints MiniLang spellings |
| 6 | `1/0` crashed with a Python `ZeroDivisionError` traceback | No check | Explicit check, raising `MiniLangRuntimeError("division by zero")` |
| 7 | Deep recursion crashed with Python's `RecursionError` | No limit | `RuntimeLimits.max_call_depth` (section 3.6) |
| 8 | `"a" + "b"` was rejected | The type checker only allowed numbers for `+` | `string + string` → string |

The **TDD loop** for each fix: write a test describing correct behavior → watch it fail (*red*) → fix → watch it pass (*green*). Seeing it fail first proves the test can detect the bug. A test that has never failed might be testing nothing.

Another Python leak worth knowing: in Python `True == 1` is `True`, because `bool` is a subclass of `int`. `values_equal()` checks types first so MiniLang's `true == 1` is `false`. `type_name()` checks `bool` before `int` for the same reason.

### 3.4 Errors with positions

Every error now carries a `stage`, `line`, `col` and a bare `message`, and renders as:
```
error[semantic]: variable 'y' used before declaration
 --> prog.ml:2:7
  |
2 | print(y);
  |       ^
```

**How positions reach semantic and runtime errors with almost no code change:** AST nodes record the position of their first token. The analyzer's central `analyze(node)` method wraps every visit:
```python
try:
    return method(node)
except SemanticError as error:
    error.attach_position(node.line, node.col)  # only if not already set
    raise
```
As the exception bubbles up the tree, the **innermost** node attaches its position first and outer nodes leave it alone. So the error points at the most specific construct (the `y`, not the whole `print` statement), and none of the 25 `raise` sites had to change. The runtime uses the same trick.

**Missing semicolons point at the right place.** If `;` is missing at the end of line 1, the parser only notices on line 2 when it sees `print`. Reporting line 2 confuses people. The parser remembers the previous token and reports *just after it* (line 1, col 10). That's where the programmer has to type, and it's how `rustc` does it.

**Errors as data.** `to_dict()` gives `{"stage", "message", "line", "col"}`, and `run_source()` returns a `RunResult` instead of raising. Tools (the CLI's `--json`, the LLM agent, the MCP server) want a value they can inspect, not an exception they must catch.

### 3.5 The CLI and exit codes

`minilang run | check | compile | demo`, with `-` for stdin, `--json`, and `--emit tac asm`. Diagnostics go to **stderr** and program output to **stdout**, so `minilang run x.ml > out.txt` captures only the program's output.

Exit codes: `0` ok, `1` compile error, `2` usage error, `3` runtime error. Runtime errors are 3, not 2, because Python's `argparse` already exits with 2 on bad arguments, and scripts need to tell those apart.

### 3.6 Runtime limits

`RuntimeLimits(max_steps=1_000_000, max_call_depth=500, max_output_lines=10_000)`:
- **Steps:** every executed statement increments a counter, which stops `while (true) {}`.
- **Call depth:** a counter incremented in `call_function` and decremented in `finally` (so it resets even when `return` unwinds via an exception).
- **Output lines:** stops `while (true) { print(1); }` from eating memory.

**Python's own recursion limit.** A tree-walking interpreter recurses in Python for every nested construct. We *measured* it: each MiniLang call uses about 10 Python stack frames. 500 MiniLang calls need about 5,000 frames, but Python's default limit is 1,000. So `run()` temporarily raises the limit with a context manager (restored in `finally`), allowing 30 frames per call for headroom, and converts any remaining `RecursionError` into a clean MiniLang error.

**Why it mattered:** Phase 2 runs code written by LLMs. Untrusted code needs resource limits. This is the same idea as timeouts and memory caps in a production sandbox.

### 3.7 Testing strategy

| Kind | Example | Purpose |
|---|---|---|
| Golden | `test_golden.py` | Pins whole-pipeline output; made the refactor safe |
| Regression | `test_regressions.py` | One test per bug; stops it coming back |
| Unit | `test_lexer.py`, `test_parser.py`, ... | Pinpoints which stage broke |
| CLI / integration | `test_cli.py` | Exit codes, stdout vs stderr, `--json`, stdin |
| Docs | `test_docs.py` | Runs every ```` ```js ```` example in the README and spec, so docs can't drift from the code |

Patterns used: **AAA** (Arrange, Act, Assert), `@pytest.mark.parametrize` for tables of cases, and fixtures (`capsys` for printed output, `tmp_path` for files, `monkeypatch` for environment variables). A neat trick in `test_parser.py`: precedence is checked by rendering the tree as an s-expression, e.g. `1 + 2 * 3` must become `(+ 1 (* 2 3))`.

### 3.8 CI

`.github/workflows/ci.yml` runs on every pull request: ruff lint and format check, then pytest with a coverage gate (≥ 80%) on Python 3.10, 3.11, 3.12 and 3.13 (a **matrix** build), then a CLI smoke test.

### 3.9 Environment gotcha: iCloud Desktop

Your Desktop syncs to iCloud, which sets the macOS `hidden` flag on files inside `.venv`. Python 3.12+ ignores hidden `.pth` files, so `pip install -e .` silently stopped working (`ModuleNotFoundError: minilang`). The fix: the real environment lives in `.venv.nosync` (iCloud skips `*.nosync`), with a `.venv` symlink pointing at it. The diagnosis came from `ls -lO`, which shows file flags. Reading the environment, not just the code, is a big part of debugging.

---

## 4. Phase 2: the LLM benchmark

### 4.1 The research question

> Can a model write correct code in a language it has never seen, from the spec alone, and how much does **error-message quality** help it repair mistakes?

### 4.2 Eval design decisions

- **The model sees the expected output** (like a test case); the reference solution stays hidden. That keeps the task about *writing MiniLang*, not guessing the output format.
- **Every task has a reference solution that a test runs.** That's how we caught two of our own tasks being impossible as first written (section 4.9). An unsolvable task silently caps every model's score.
- **A deterministic grader:** run the submitted program and compare printed lines exactly. There's no LLM judge, so there's no judge bias.
- **Four feedback conditions** (`bench/feedback.py`): `oneshot` (no tool), `opaque` ("the program failed"), `message` (error text only), and `diagnostic` (full positioned snippet). Changing only the feedback is a **controlled experiment**: one variable changes, everything else stays fixed.
- **Price-matched model pairs:** Haiku 5.5 vs GPT-6 Luna ($0.10/$0.50) and Sonnet 5.5 vs GPT-6.1 Sol ($2/$10), plus a free local Qwen 3B. Comparing models at the same price is the question a customer actually asks.
- **Same reasoning effort (`medium`) for every hosted model**, and **no refusal fallbacks**: a fallback would let a different model answer and contaminate the result.

### 4.3 The agent loop (`bench/agent.py`)

```
send task ─▶ model turn
  ├─ refusal                 → outcome "refusal"
  ├─ no tool calls           → grade the code block in its reply (or the last program it ran)
  └─ tool calls:
       run_minilang(code)    → compile + run → feedback for this condition (max 5 runs)
       submit_solution(code) → grade it → done
     send all tool results back in ONE message → next model turn (max 8 turns)
```

We wrote this **manual loop** instead of using the Anthropic SDK's Tool Runner because the same loop drives three different APIs and has to count every run for the metrics. The Tool Runner is the right default when you only use Claude and don't need that control.

### 4.4 One interface, three APIs: the adapter pattern

`ChatSession` (`bench/llm/base.py`) is a two-method protocol: `send_user(text)` and `send_tool_results(results)`, both returning a normalized `Turn(text, tool_calls, stop, usage)`. Each provider gets an adapter:

| | Anthropic Messages | OpenAI Responses | Chat Completions (Ollama) |
|---|---|---|---|
| Tool definition | `{name, input_schema, strict}` | `{type:"function", name, parameters, strict}` | `{type:"function", function:{name, parameters}}` |
| Model calls a tool | `tool_use` content block | `function_call` output item | `message.tool_calls[]` |
| Tool result goes back as | `tool_result` block in a **user** message | `function_call_output` item | message with `role:"tool"` |
| Hidden reasoning | thinking blocks (send back unchanged) | reasoning items (send back) | n/a |
| System prompt | `system=` | `instructions=` | first message, `role:"system"` |

**Provider-native history:** each adapter stores the conversation in its own API's format and appends the raw response. The alternative, translating everything to a shared format and back, would lose Claude's thinking blocks, which the API requires to be returned unchanged on the next turn.

### 4.5 Real API differences we hit

1. **GPT-6 rejected tools + reasoning on Chat Completions:** *"Function tools with reasoning_effort are not supported ... use /v1/responses or set reasoning_effort to 'none'."* Turning reasoning off would make the comparison unfair (Claude thinks), so we added a Responses API adapter. "OpenAI-compatible" covers several APIs.
2. **Claude 5.5 models reject forced tool choice** (`tool_choice: any`/`tool` → 400). We use `auto` plus clear instructions, and `strict: true` so tool inputs always match the schema.
3. **MCP Python SDK 2.x renamed `FastMCP` to `MCPServer`.** We inspected the installed package instead of writing v1 code from memory. Check the version you actually have.
4. **The SDKs are built on `httpx2`, not `httpx`.** A test that imported `httpx` to build a fake error failed until we switched.

### 4.6 Cost engineering

- **Prompt caching:** the ~3K-token spec is resent on every turn. Anthropic gets `cache_control={"type":"ephemeral"}`, and OpenAI caches automatically. Cached input costs about 0.1× the normal price. The smoke test showed it working: ~3,200 tokens read from cache on the second turn.
- **Cost accounting:** `Price.cost(usage)` bills uncached input, cache reads (0.1×), cache writes (1.25×) and output separately.
- **The episode cache:** each finished episode is saved under a **fingerprint** (a SHA-256 hash of the model, task, condition, sample, full system prompt and limits). Re-running costs nothing for finished work, and *any* change to the prompt changes the hash, so stale results are never reused. API errors are deliberately not cached, so they get retried.
- **`--dry-run`** estimates cost before spending anything.
- **Concurrency:** a thread pool runs episodes in parallel, with a **semaphore per model** (`max_concurrency`) so the local Ollama model runs one at a time while hosted APIs run up to 4.

### 4.7 Statistics: Wilson confidence intervals

With 32 tasks per cell, a pass rate of 90% vs 85% may just be noise. The report shows a **Wilson 95% interval** for each rate. It's better than the textbook `p ± 1.96·√(p(1−p)/n)` interval at small n or near 0%/100%, where the simple version can go below 0 or above 100%. Rule of thumb: if two intervals overlap a lot, don't claim a difference.

### 4.8 The MCP server

`minilang-mcp` exposes `run_program`, `check_program` and `compile_program` as MCP tools, and the spec as the resource `minilang://spec`. **MCP** (Model Context Protocol) is a standard way for AI apps (Claude Desktop, Claude Code, IDEs) to discover and call external tools. The tools are annotated `readOnlyHint` / `idempotentHint`, which tells clients they're safe to call without asking. Inputs over 100K characters are rejected. Tests cover the functions directly *and* a real stdio round trip with the SDK's client.

### 4.9 What the first run taught us

1. **Two of our own tasks were impossible as written.** `n = n / 2` fails when `n` started as an int, because `/` returns a float and a variable's type is fixed. The reference-solution test caught it before any model saw the task.
2. **Ceiling effect:** frontier models solved almost everything in tiers 1–3, which left too few failures to measure repair. We added **tier 4**, which combines the traps, and they solved that too (112/112, even one-shot). Making small tasks harder didn't move the ceiling.
3. **Some models don't test their code.** The first failures were all Claude Sonnet submitting without running its code once, then falling into the float-division trap. Feedback can't help a model that never asks for it, hence the *Tested first* metric.

---

## 5. Results

Run `v2`: 640 graded episodes (5 models × 32 tasks × 4 conditions × 1 sample), about **$1.30** total.

| Model | Pass rate | One-shot | Tested first | Cost per solve |
|---|---|---|---|---|
| Claude Haiku 5.5 | 100% (128/128) | 32/32 | 97% | $0.0005 |
| GPT-6 Luna | 100% (128/128) | 32/32 | 100% | $0.0002 |
| GPT-6.1 Sol | 100% (128/128) | 32/32 | 100% | $0.0025 |
| Claude Sonnet 5.5 | 98% (125/128) | 32/32 | 35% | $0.0070 |
| Qwen 2.5 3B (local) | 32% (41/128) | 9/32 | 73% | free |

Pooled repair rates: opaque 40% (6/15), message 24% (4/17), diagnostic 33% (5/15). The 95% intervals overlap heavily (roughly 10–64%).

**What the results say:**

1. **Frontier models learned MiniLang from the spec alone.** 509/512 episodes passed, including all 128 one-shot episodes where they couldn't run their code at all.
2. **Error-message quality had no measurable effect: a null result.** It is still informative, because *why* it's null is the finding:
   - Hosted models failed a first run only 14 times in 384 tool episodes and repaired all of them, even with "the program failed". For a strong model, *any* failure signal is enough: it rereads the spec and finds its own mistake.
   - Qwen 3B repaired 1 of 33. Its errors were mostly syntax from other languages (`array[i]`, `.method()`, `for i in`, `break`, `?:`), and it re-ran code in only 22 of 70 tool episodes. A model that doesn't iterate gets nothing from better messages.
   - So error quality probably matters most for **mid-size models** (roughly 7–14B), capable enough to act on a hint but not strong enough to need none. That's the obvious next experiment.
3. **Testing habits beat raw capability.** Every hosted-model failure was Claude Sonnet submitting without running its code (it tested in only 35% of episodes). It did worse than the cheaper Claude Haiku at about 14× the cost per solve.
4. **The cheapest models were the best value:** GPT-6 Luna at $0.0002 and Claude Haiku at $0.0005 per solved task, both at 100%.

**How to present a null result honestly:** say what you expected, what you measured, the uncertainty, and the most likely explanation. "No detectable effect at n≈15 failures per condition" is a different claim from "error messages don't matter". The second claim isn't supported.

---

## 6. Key terms

| Term | Meaning |
|---|---|
| Lexer / token | Turns characters into tokens (`KW(let)`, `IDENT(x)`, `INT(5)`); tracks line and column |
| Maximal munch | The lexer takes the longest operator that matches: `==` not `=` `=` |
| Recursive descent | A parser with one function per grammar rule, calling each other recursively |
| AST | Abstract syntax tree: the program's structure without punctuation |
| Precedence / associativity | Which operator binds tighter (`*` over `+`), and how equal ones group (`a-b-c` = `(a-b)-c`) |
| Symbol table / scope | Names declared in each block; inner scopes chain to outer ones |
| Gradual typing | Some types are known statically, unknown ones are checked at run time |
| Three-address code (TAC) | An intermediate form with at most one operator per instruction: `t1 = b * c` |
| Tree-walking interpreter | Executes by visiting AST nodes directly, without compiling to machine code |
| Closure | A function plus the environment it was defined in |
| Characterization / golden test | A test that records current behavior to protect a refactor |
| Regression test | A test that reproduces a fixed bug so it can't come back |
| Coverage | Percentage of code lines executed by the tests |
| CI matrix | Running the same checks on several Python versions in parallel |
| Tool calling | A model asks your code to run a function and gets the result back |
| Agent loop | Model → tool call → result → model ..., until done |
| Adapter pattern | Wrapping different interfaces behind one common interface |
| Prompt caching | The provider reuses a previously processed prompt prefix at reduced cost |
| Eval / benchmark | A repeatable measurement of model behavior on fixed tasks |
| Ceiling effect | The tasks are so easy that everyone scores near 100%, hiding differences |
| Confidence interval | The range the true rate plausibly lies in, given the sample size |
| MCP | Model Context Protocol: a standard for exposing tools and data to AI apps |
| Idempotent | Calling it twice has the same effect as calling it once |

---

## 7. Interview questions and answers

**Compiler and engineering**

1. **Walk me through what happens when MiniLang runs `print(1 + 2 * 3);`.**
   The lexer produces tokens: `KW(print) SEP(() INT(1) OP(+) INT(2) OP(*) INT(3) SEP()) SEP(;)`. The parser builds `Print(BinaryOp(+, 1, BinaryOp(*, 2, 3)))`, because `factor` (the `*` level) is called from `term` (the `+` level), so `*` groups first. The semantic analyzer infers int and int → int. The code generator emits `t1 = 2 * 3`, `t2 = 1 + t1`, `print t2`. The interpreter evaluates the tree and prints `7`.

2. **How did you refactor 1,400 lines without breaking anything?**
   With characterization (golden) tests first: snapshots of the old compiler's tokens, AST, TAC and output for 5 programs. The refactored package had to reproduce them exactly. Bug fixes came afterwards, in separate commits, each starting with a failing test.

3. **How does the semantic analyzer report the exact column without changing every `raise`?**
   AST nodes carry positions. The central `analyze()` method catches `SemanticError` and attaches the current node's position only if none is set yet. The innermost node handles it first, so it wins.

4. **What is gradual typing and why did you choose it?**
   Types known at compile time (literals, variables) are checked statically. Function parameters are `unknown` and are checked at run time. The language has no type annotations, so without this every function comparing a parameter was rejected (bug #1).

5. **Why does your interpreter change Python's recursion limit?**
   A tree-walking interpreter uses Python's call stack. We measured about 10 Python frames per MiniLang call, so the 1,000-frame default caps MiniLang at about 100 calls. We raise it temporarily during a run (restored in `finally`) and enforce our own `max_call_depth`.

6. **Why limits at all?**
   The benchmark runs code written by LLMs, which is untrusted. An infinite loop must become an error message, not a hung process. It's the same reasoning as timeouts in a production sandbox.

7. **Why do runtime errors exit with code 3?**
   `argparse` exits with 2 on bad arguments, and scripts calling the CLI need to tell a usage mistake from a crashing program.

8. **Why does `run_source` return a result instead of raising?**
   Its callers (the CLI's JSON mode, the agent, the MCP server) all want to report errors as data. Converting at the boundary once keeps every caller simple.

**AI engineering**

9. **Explain your agent loop.**
   Send the task, then loop: if the model asks for `run_minilang`, compile and run the code and return feedback; if it calls `submit_solution`, grade it and stop. All results from one turn go back in a single message. It's capped at 5 runs and 8 turns.

10. **How did you support three LLM providers?**
    Adapter pattern: one `ChatSession` protocol, three adapters (Anthropic Messages, OpenAI Responses, Chat Completions for Ollama). Each keeps provider-native history and returns a normalized `Turn`.

11. **Why keep provider-native history instead of a common message format?**
    Claude may return thinking blocks that must be sent back unchanged on the next request, and OpenAI returns reasoning items. Translating to a common format and back would drop or corrupt them.

12. **Why did you use OpenAI's Responses API rather than Chat Completions?**
    GPT-6 rejected function tools combined with reasoning on Chat Completions. Disabling reasoning would have made the comparison with Claude unfair, so we used the endpoint that supports both.

13. **How did you keep the comparison fair?**
    Price-matched pairs, the same reasoning effort, the same prompt, tools and limits, no refusal fallbacks to other models, and a deterministic grader.

14. **How did you control cost?**
    A dry-run estimate before spending, prompt caching for the repeated spec, an on-disk episode cache keyed by a content hash, cheap models for most of the matrix, and cost tracked per episode, including cache pricing.

15. **What's the difference between pass rate and repair rate, and why does the second matter?**
    Pass rate mixes "got it right first time" with "fixed it after feedback". Repair rate only looks at episodes whose first run failed, so it isolates the effect of the feedback, which is what the conditions vary.

16. **How do you know a difference is real?**
    Wilson 95% intervals on every rate. With about 32 tasks per cell, I only claim differences whose intervals don't overlap much. Otherwise I say the result is inconclusive and run more samples.

17. **Your first benchmark showed nearly 100% for top models. What did you do?**
    I recognized a ceiling effect: no failures means nothing to measure. I added a harder tier combining the language's traps, and frontier models solved that too. So I reported it honestly: frontier models learn the language from the spec alone, and the feedback experiment needs larger tasks or mid-size models to produce enough failures.

18b. **Your main hypothesis came out null. Is the project a failure?**
    No. A null result with a clear explanation is a finding. Strong models repaired every failure even with minimal feedback, and the 3B model couldn't repair with any feedback. That points to a specific next experiment (mid-size models), and I report the confidence intervals so nobody over-reads it. Being able to say "the data doesn't support my hypothesis, and here's why" matters a lot in customer-facing AI work.

18. **What surprised you?**
    One frontier model often submitted without testing its code at all, even with a run tool available, and failed on a trap that testing would have caught. Tool *availability* doesn't guarantee tool *use*, so I added a metric for it.

19. **What is MCP and what did you build with it?**
    The Model Context Protocol is a standard way for AI apps to discover and call tools. `minilang-mcp` exposes run, check and compile tools plus the spec as a resource, so Claude Desktop or Claude Code can write and test MiniLang directly.

20. **How did you test code that calls paid APIs without paying?**
    Fake sessions that replay scripted turns (for the agent loop) and fake SDK clients that return SDK-shaped objects (for the adapters). Only a small smoke test hit the real APIs.

**Behavioral / FDE-style**

21. **Tell me about a time a tool or API didn't behave as expected.**
    The OpenAI 400 error on tools + reasoning; the MCP SDK's 2.x rename; iCloud hiding `.pth` files. In each case I read the actual error or installed package and changed course, rather than guessing.

22. **How would you explain this project to a non-technical stakeholder?**
    "I built a small programming language and its compiler, then tested whether AI models can learn it from the manual alone. The experiment shows how much clear error messages help AI fix its own mistakes, which matters for any company building AI coding tools."

---

## 8. How to talk about it

**Resume bullets:**

- Built a compiler from scratch in Python (lexer, recursive-descent parser, gradual type checker, three-address code, sandboxed interpreter) with 313 tests, 97% coverage and CI on Python 3.10–3.13
- Built a multi-provider LLM evaluation harness (Anthropic, OpenAI, Ollama) where models write code in a never-seen language through a compiler-as-a-tool agent loop; adapter pattern over the Messages, Responses and Chat Completions APIs, with prompt and result caching (640 episodes for about $1.30)
- Found that frontier models learned the language from its spec alone (509/512 passed, 100% one-shot), while a 3B model solved 32%; every frontier failure was an untested submission, from a model that tested its code only 35% of the time
- Exposed the compiler to AI assistants as an MCP server (run/check/compile tools + spec resource), tested over a real stdio connection

**60-second pitch:** "I took my compiler class project and turned it into two things. First, real software: a tested Python package with positioned error messages, a CLI and CI. Then I used it as an AI evaluation tool. Since nobody else has my language, models have to learn it from the spec. I built an agent loop where Claude, GPT and a local model write code, run it through my compiler and fix their mistakes. The frontier models learned the language almost perfectly from the spec alone. The interesting failures came from one model that often skipped testing its code. My hypothesis that better error messages would help came out null, and I can explain why. Along the way I handled real integration issues, like OpenAI needing a different API for tools with reasoning, and I exposed the compiler as an MCP server so AI assistants can use it directly."

---

## 9. What could come next

- Run mid-size open models (e.g. Qwen 2.5 Coder 7B/14B via Ollama), where error quality is most likely to matter
- Larger, multi-function tasks that produce more first-run failures
- More samples per task to tighten confidence intervals
- A web playground (FastAPI + a page showing each compiler stage), deployed with a public link
- Bytecode compilation and a VM, to compare performance with the tree-walker
- A prompt experiment: does adding "always test before submitting" change the *Tested first* rate and the pass rate?
