# MiniLang showcase site

The project's website: an overview, a **playground** that runs the real compiler in the browser, the
**benchmark analysis** with charts, and an **episode explorer** for all 890 graded runs.

Live: https://ronish645.github.io/minilang-compiler/

## Run it locally

```bash
# from the repo root: export the benchmark results as JSON (writes site/public/data/)
.venv/bin/python -m bench.export

cd site
npm install
npm run dev          # copies the compiler into public/py/, then starts Vite
npm run build        # type-check + production build into site/dist/
```

## How it fits together

| Piece | What it does |
|---|---|
| `bench/export.py` | Turns `bench/results/*/episodes.jsonl` into `summary.json`, `episodes.json` and `tasks.json`, reusing the report's metrics so the site and `REPORT.md` can't disagree |
| `scripts/copy-compiler.mjs` | Copies `minilang/*.py` into `public/py/` for Pyodide |
| `src/features/playground/worker/` | A Web Worker that loads Pyodide (Python compiled to WebAssembly) and calls `minilang.playground.explore()` |
| `src/features/benchmark/` | Charts built from HTML/CSS with one shared tooltip, each with a table view |
| `src/features/explorer/` | Filterable episode list; every filter lives in the URL |
| `src/components/`, `src/lib/` | Shared UI components, design tokens, typed data loading |
| `.github/workflows/site.yml` | Builds on every PR; deploys to GitHub Pages from `main` |

Design tokens live in `src/styles.css`. Model colors come from a palette validated for color-vision
deficiency in light and dark mode; each model keeps one color on every chart.
