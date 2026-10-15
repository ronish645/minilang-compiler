import { Cpu, Layers, PackageCheck } from "lucide-react";
import type { ReactNode } from "react";

const POINTS: { icon: ReactNode; title: string; body: string }[] = [
  {
    icon: <Cpu className="size-4" aria-hidden />,
    title: "Python, compiled to WebAssembly",
    body: "Pyodide runs CPython in the browser. The compiler's .py files are loaded into its virtual file system and imported as-is.",
  },
  {
    icon: <Layers className="size-4" aria-hidden />,
    title: "Off the main thread",
    body: "Compiling happens in a Web Worker, so the page stays responsive. A watchdog replaces the worker if a run takes over 8 seconds.",
  },
  {
    icon: <PackageCheck className="size-4" aria-hidden />,
    title: "The same package as the CLI",
    body: "This is the tested minilang package the CLI, the test suite and the LLM benchmark use. Nothing is reimplemented in JavaScript.",
  },
];

export function HowItWorks() {
  return (
    <section aria-labelledby="how-it-works" className="mt-10">
      <h2 id="how-it-works" className="text-sm font-semibold uppercase tracking-[0.14em] text-muted">
        How it works
      </h2>
      <ul className="mt-4 grid gap-4 sm:grid-cols-3">
        {POINTS.map((point) => (
          <li key={point.title} className="rounded-2xl border border-border bg-surface p-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-ink">
              <span className="grid size-7 place-items-center rounded-lg bg-accent-soft/60 text-accent-ink">
                {point.icon}
              </span>
              {point.title}
            </div>
            <p className="mt-2 text-sm text-ink-2">{point.body}</p>
          </li>
        ))}
      </ul>
    </section>
  );
}
