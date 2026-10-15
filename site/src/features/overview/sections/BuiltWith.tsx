import { BookOpen, ExternalLink, FlaskConical, NotebookPen } from "lucide-react";
import { GitHubIcon } from "../../../components/ui/GitHubIcon";
import { BENCH_URL, REPO_URL, SPEC_URL } from "../../../lib/links";

const STACK = [
  "Python",
  "pytest",
  "Anthropic API",
  "OpenAI Responses API",
  "Ollama",
  "MCP",
  "React",
  "TypeScript",
  "Pyodide",
  "Tailwind CSS",
];

const NOTES_URL = `${REPO_URL}/tree/main/docs/notes`;

const LINKS = [
  { href: REPO_URL, label: "Source code", icon: <GitHubIcon className="size-4" /> },
  { href: SPEC_URL, label: "Language spec", icon: <BookOpen className="size-4" aria-hidden /> },
  { href: BENCH_URL, label: "Benchmark method", icon: <FlaskConical className="size-4" aria-hidden /> },
  { href: NOTES_URL, label: "Build notes", icon: <NotebookPen className="size-4" aria-hidden /> },
];

export function BuiltWith() {
  return (
    <div className="flex flex-col gap-8 rounded-2xl border border-border bg-surface-2/60 p-5 sm:p-8 lg:flex-row lg:items-center lg:justify-between">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-[0.14em] text-ink-2">Built with</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {STACK.map((item) => (
            <li
              key={item}
              className="rounded-full border border-border bg-surface px-3 py-1 text-sm text-ink-2"
            >
              {item}
            </li>
          ))}
        </ul>
      </div>
      <ul className="grid shrink-0 grid-cols-2 gap-2 sm:flex sm:flex-wrap">
        {LINKS.map((link) => (
          <li key={link.label}>
            <a
              href={link.href}
              target="_blank"
              rel="noreferrer"
              className="inline-flex w-full items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-ink transition hover:border-border-strong"
            >
              {link.icon}
              {link.label}
              <ExternalLink className="ml-auto size-3.5 text-muted sm:ml-0" aria-hidden />
              <span className="sr-only">(opens in a new tab)</span>
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
