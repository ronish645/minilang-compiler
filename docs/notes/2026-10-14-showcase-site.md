# The Showcase Site: Build Notes

**Date:** 2026-10-14 · **Author:** Ronish Shrestha · **Branch:** `feat/showcase-site` · **Previous notes:** [MiniLang v2.1](2026-10-14-minilang-v2.1.md)

The project had good results but no way to *show* them quickly: a recruiter won't clone a repo, and a table in a README doesn't tell a story. Today we built a website with four pages: an overview, a **playground** that runs the real compiler in the browser, a **benchmark analysis** page with charts, and an **episode explorer** for all 890 graded runs. These notes explain the architecture, the decisions behind it, and how the work was split across parallel agents.

---

## 1. Architecture at a glance

```
bench/results/*/episodes.jsonl ──▶ bench/export.py ──▶ site/public/data/*.json ──┐
                                                                              ├─▶ React app (Vite) ──▶ GitHub Pages
minilang/*.py ──▶ scripts/copy-compiler.mjs ──▶ site/public/py/ ──▶ Pyodide (Web Worker)
```

| Layer | Choice | Why |
|---|---|---|
| Hosting | GitHub Pages (static) | Free, no server to secure or keep running |
| Build | Vite + React 19 + TypeScript (strict) | The standard stack; components and type safety for 117 files |
| Styling | Tailwind CSS v4 + design tokens | One set of semantic colors (`bg-surface`, `text-ink-2`) that swap for dark mode |
| Compiler in the browser | Pyodide (CPython compiled to WebAssembly) in a Web Worker | Runs the *same* Python package the tests cover; no backend |
| Charts | Hand-built HTML/CSS components | Exact control over the chart rules; 16 kB gzipped for the whole page |
| Data | JSON generated from the raw results by Python | One source of truth (see §2) |

**Why no backend?** A FastAPI server could run the compiler too, but then it would have to be hosted, paid for and secured against strangers running code on it. With Pyodide, untrusted code runs in the *visitor's* browser sandbox, the hosting is free, and the site can't go down because a server did. The trade-off is a ~10 MB download on the first visit, which the playground handles with a loading state while the editor already works.

---

## 2. The data pipeline: one source of truth

`bench/export.py` reads the raw episodes and writes three files:

| File | Contents | Used by |
|---|---|---|
| `summary.json` (23 kB) | Pre-computed metrics: pass, repair and tested rates with 95% Wilson intervals, cost, outcomes, error patterns | Overview, Benchmark |
| `episodes.json` (470 kB) | Every episode, slimmed down (code, output, error, per-run results, cost) | Explorer |
| `tasks.json` (8 kB) | Task prompts and expected output, **without** the hidden reference solutions | Explorer |

The key decision: **the exporter reuses `bench.report`'s functions** (`pass_rate`, `repair_rate`, `Rate.wilson_interval`, the price model). The numbers on the website and in `REPORT.md` come from the same code, so they can't disagree. The site never re-implements statistics in JavaScript.

Two runs are kept apart everywhere (`v2`: tiers 1–4 on language v1; `v21-tier5`: tier 5 on v2.1). Pooling them would mix two versions of the spec, so every chart has a run selector.

Error messages are grouped into **patterns** so the chart can count them: `"Syntax error at line 3, col 9: expected ';' but found '.'"` becomes `"expected ';' but found '.'"`, and identifiers become `'…'` (two regexes in `error_pattern`).

The generated JSON is **not committed**: CI runs the exporter before every build, so the site always reflects the committed results.

---

## 3. The playground: Python in the browser

### 3.1 A JSON-ready compiler API

The existing `compile_source()` returns pretty-printed strings and raises on the first failure. A UI needs structure, and it needs the stages that worked *before* the failure (tokens are still useful when parsing fails). So we added `minilang/playground.py`:

```python
def explore(source) -> dict:
    # tokens → ast → check → codegen → run, each timed;
    # on MiniLangError: record failed_stage + every error, keep what succeeded
```

It returns `tokens` as `{type, value, line, col}`, the `ast` as a nested dict, `tac`, `asm`, `output`, every error with its `hint`, and `timings_ms` per stage. It has a lower step limit than the CLI (200,000), because Python in WebAssembly is slower. It has 9 tests, including "a syntax error keeps the tokens" and "a runaway loop is stopped".

### 3.2 Why a Web Worker

JavaScript in the browser runs on one main thread, which also paints the page. If Python ran there, every compile would freeze scrolling and typing. A **Web Worker** is a background thread with its own event loop. The page and the worker talk only through messages:

```
page ──{ id: 7, type: "explore", source }──▶ worker (Pyodide + minilang)
page ◀──{ id: 7, type: "result", json }──── worker
```

Three details make it robust:
- **Request ids.** A reply to an old request is ignored, so a slow result can't overwrite a newer one.
- **"Latest wins."** While one compile runs, only the newest edit waits; fast typing never builds a queue.
- **A watchdog.** If a request takes over 8 s, the page kills the worker and starts a fresh one. The compiler's step limit should always fire first; the watchdog covers anything else.

Results cross the boundary as a **JSON string**, so no Python objects leak into JavaScript (no proxy lifetimes to manage).

### 3.3 Live feedback

Each compile takes about 1–14 ms in Pyodide, so the playground re-runs the whole pipeline 350 ms after you stop typing (a **debounce**). Errors appear as wavy underlines in the editor (CodeMirror decorations at the error's line and column). A **pipeline strip** shows Lexer → Parser → Type checker → Codegen → Interpreter with ✓/✗ and the time of each stage, so the compiler's architecture is visible as you type. Programs can be shared: the source is base64url-encoded into `?code=`.

---

## 4. The benchmark page: charts that follow rules

The charts follow a data-visualization method with checks instead of taste (loaded from the `dataviz` skill):

1. **Pick the form from the data's job.** Magnitude across two categories → a heatmap. One estimate with uncertainty → a dot with interval whiskers. Composition → 100%-stacked bars. A single headline → a stat tile, not a chart.
2. **Color by job.**
   - **Identity** (which model): 5 fixed categorical colors. Haiku is always blue, on every chart, whatever is filtered. The rule is "color follows the entity, never its rank."
   - **Magnitude** (pass rate): one blue ramp, light to dark.
   - **State** (passed / wrong output / compile error): the reserved status colors, always with an icon and a label.
3. **Validate the palette with a script, not by eye.** The validator simulates color-vision deficiencies and measures color distance (ΔE in OKLab). Our 5 model colors pass in light and dark mode. Three light-mode colors are below 3:1 contrast, which triggers the **relief rule**: every chart has visible labels *and* a Chart/Table toggle with an accessible data table.
4. **No 5-color scatter plots.** With all pairs on screen, only 3 colors stay distinguishable for color-blind readers, so cost uses sorted, labelled bars instead.

**Takeaways are computed, not written by hand.** For example, the testing section names the model that tested least, and adds "all N hosted failures were its untested submissions" *only if the data says so*. Switch runs and the sentences change with the numbers.

---

## 5. The explorer: state in the URL

All 890 episodes, with filters (run, model, condition, outcome, task, search). Every filter is stored in the URL (`useSearchParams`), so any view can be shared or bookmarked, and the browser's Back button closes an open episode. "Featured views" (*Qwen's failures*, *Sonnet's untested submissions*, *Every repair*) are just filter presets.

The episode drawer is a proper **modal dialog**: focus moves into it, Tab is trapped inside, Esc closes it, and focus returns to the row that opened it. It shows the task, the submitted program, the run timeline (✗ syntax → ✓), and the output next to the expected output, with mismatched lines highlighted. It is honest about the data: we stored the final program and each run's result, not the whole conversation.

---

## 6. How the work was parallelized

| Step | Who | Why this order |
|---|---|---|
| Data exporter + playground API (Python, TDD) | me | Every page depends on these contracts |
| Foundation: tokens, layout, UI components, typed loaders, router | me | Shared code must exist **before** parallel work, or three agents invent three button styles |
| Playground · Benchmark · Overview + Explorer | 3 agents in parallel | Each owned its own folder; shared files were read-only |
| Integration, visual check, code review | me + a review agent | One place to apply shared changes and catch inconsistencies |

The rules that made parallel work safe:
- **Disjoint file ownership:** no two agents could edit the same file.
- **No `npm install` by agents:** concurrent installs corrupt `node_modules`.
- **Separate build folders:** each agent built into its own scratch directory.
- **Requests, not edits:** an agent that needed a shared change wrote it in its report (the playground agent needed two dependencies listed and an ES-module worker setting), and I applied it once.

This is the same pattern as splitting work across a team: agree on interfaces first, then work in parallel on separate modules.

---

## 7. Deployment

`.github/workflows/site.yml`:
- **On every PR:** export the data, `npm ci`, type-check and build. A broken site can't be merged.
- **On `main`:** the same build, then deploy to GitHub Pages with the official `deploy-pages` action.

The site uses a `HashRouter` (`#/benchmark`), because GitHub Pages serves static files only and would return 404 for a real `/benchmark` path. Vite's `base: "/minilang-compiler/"` matches the Pages URL.

---

## 8. Key terms

| Term | Meaning |
|---|---|
| **WebAssembly (Wasm)** | A binary format browsers run at near-native speed; CPython is compiled to it |
| **Pyodide** | CPython + a standard library compiled to WebAssembly, with a JS ↔ Python bridge |
| **Web Worker** | A background thread in the browser; talks to the page only by messages |
| **Debounce** | Wait until input has been quiet for N ms before acting |
| **Design tokens** | Named design values (`--surface`, `--ink-2`) that components use instead of raw colors |
| **CVD (color-vision deficiency)** | Protanopia, deuteranopia, tritanopia; palettes are checked by simulating them |
| **ΔE (OKLab)** | A measure of how different two colors look; the palette needs ≥ 8 under CVD simulation |
| **Wilson interval** | A 95% confidence interval for a proportion that behaves well with small n |
| **Static site / SPA** | Pre-built files only; the browser does all the work |
| **HashRouter** | Client-side routing in the `#` part of the URL, which never reaches the server |

---

## 9. Interview questions and answers

**Q: Why did you run the compiler in the browser instead of behind an API?**
No server to host, pay for or secure. The visitor's browser sandboxes the untrusted code, and it's the same Python package my tests cover, so the demo can't drift from the real compiler. The cost is a ~10 MB first load, which I handle with a loading state while the editor already works.

**Q: Why a Web Worker?**
The main thread also paints the page; running Python there would freeze typing. In a worker the UI stays responsive. Request ids drop stale replies, only the latest edit waits, and a watchdog restarts a hung worker.

**Q: How do you make sure the website's numbers are right?**
The site doesn't compute statistics. A Python exporter reuses the same functions that produce the benchmark report, with tests, and CI regenerates the JSON from the committed results on every build. Takeaway sentences are computed from that data too, so the text can't contradict the charts.

**Q: How did you choose chart colors?**
By job: fixed categorical colors for identity, a single-hue ramp for magnitude, reserved status colors with icons for outcomes. I validated the palette with a script that simulates color blindness. Where light-mode contrast was too low, every chart got direct labels and a table view.

**Q: You used AI agents to build parts of this. How did you keep it coherent?**
I built the contracts and the shared foundation first (data schema, design tokens, components, routing). Then the agents worked in parallel on separate folders with read-only shared code, and asked for shared changes instead of making them. I integrated, checked every page visually in both themes, and ran a separate review pass. It's the same discipline as a team: interfaces first, clear ownership, one integrator.

---

## 10. What's next

- After merging: enable GitHub Pages (Settings → Pages → Source: GitHub Actions) so the first deploy goes live.
- A 30–60 s GIF of the playground at the top of the README.
- Teach the editor MiniLang's own keywords (`fn` is currently highlighted as plain text by the JavaScript mode).
- Record full conversations in future benchmark runs, so the explorer can replay every step.
