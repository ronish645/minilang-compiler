// Copy the MiniLang compiler package into public/py/ so Pyodide can import it
// in the browser, and write a manifest of the files to load.
import { copyFileSync, mkdirSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const source = join(here, "..", "..", "minilang");
const target = join(here, "..", "public", "py", "minilang");
// Modules that need packages Pyodide doesn't ship (or a terminal) stay out.
const EXCLUDED = new Set(["mcp_server.py", "cli.py"]);

rmSync(target, { recursive: true, force: true });
mkdirSync(target, { recursive: true });
const files = readdirSync(source).filter((f) => f.endsWith(".py") && !EXCLUDED.has(f));
for (const file of files) copyFileSync(join(source, file), join(target, file));
writeFileSync(join(target, "..", "manifest.json"), JSON.stringify({ files }, null, 2) + "\n");
console.log(`copied ${files.length} compiler modules to public/py/minilang/`);
