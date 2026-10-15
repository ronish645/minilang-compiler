/// <reference lib="webworker" />
// Runs the real MiniLang compiler (Python) inside Pyodide, off the main thread,
// so a slow or runaway program can never freeze the page.
import type { ExploreResult, WorkerRequest, WorkerResponse } from "./protocol";

// Pinned so a new Pyodide release can't change behavior under us.
const PYODIDE_VERSION = "314.0.7";
const PYODIDE_URL = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
const PACKAGE_DIR = "/home/pyodide/minilang";

// Just the slice of the Pyodide API this worker uses.
interface PyCallable {
  (source: string): string;
}
interface Pyodide {
  version: string;
  FS: {
    mkdirTree(path: string): void;
    writeFile(path: string, data: string): void;
  };
  runPython(code: string): unknown;
}
interface PyodideModule {
  loadPyodide(options: { indexURL: string }): Promise<Pyodide>;
}

const scope = self as unknown as DedicatedWorkerGlobalScope;
const post = (message: WorkerResponse) => scope.postMessage(message);

const assetBase = new URL(`${import.meta.env.BASE_URL}py/`, scope.location.origin);

async function fetchText(path: string): Promise<string> {
  const response = await fetch(new URL(path, assetBase));
  if (!response.ok) throw new Error(`could not load ${path} (HTTP ${response.status})`);
  return response.text();
}

/** Copy the compiler's .py files (listed in manifest.json) into Pyodide's virtual FS. */
async function installCompiler(pyodide: Pyodide): Promise<void> {
  const manifest = JSON.parse(await fetchText("manifest.json")) as { files?: unknown };
  if (!Array.isArray(manifest.files)) throw new Error("manifest.json has no file list");
  const files = manifest.files.filter((f): f is string => typeof f === "string");
  const sources = await Promise.all(files.map((f) => fetchText(`minilang/${f}`)));
  pyodide.FS.mkdirTree(PACKAGE_DIR);
  files.forEach((file, i) => pyodide.FS.writeFile(`${PACKAGE_DIR}/${file}`, sources[i]));
}

async function boot(): Promise<PyCallable> {
  post({ type: "progress", message: "Downloading Python runtime…" });
  const module = (await import(/* @vite-ignore */ `${PYODIDE_URL}pyodide.mjs`)) as PyodideModule;
  const pyodide = await module.loadPyodide({ indexURL: PYODIDE_URL });

  post({ type: "progress", message: "Loading compiler…" });
  await installCompiler(pyodide);
  // explore() returns a dict; json.dumps keeps the boundary a plain string,
  // which avoids leaking PyProxy objects across the JS/Python border.
  const explore = pyodide.runPython(
    [
      "import json, sys",
      "sys.path.insert(0, '/home/pyodide')",
      "from minilang.playground import explore",
      "lambda source: json.dumps(explore(source))",
    ].join("\n"),
  ) as PyCallable;
  post({ type: "ready", pythonVersion: pyodide.version });
  return explore;
}

const ready = boot();
ready.catch((error: unknown) => {
  post({ type: "error", id: null, message: `Could not start the compiler: ${describe(error)}` });
});

function describe(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

scope.onmessage = async (event: MessageEvent<WorkerRequest>) => {
  const request = event.data;
  if (request.type !== "explore") return;
  try {
    const explore = await ready;
    const result = JSON.parse(explore(request.source)) as ExploreResult;
    post({ type: "result", id: request.id, result });
  } catch (error) {
    post({ type: "error", id: request.id, message: describe(error) });
  }
};
