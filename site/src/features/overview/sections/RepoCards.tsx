import { Check, Cpu, FlaskConical, Plug, type LucideIcon } from "lucide-react";
import { Card } from "../../../components/ui/Card";
import { count } from "../../../lib/format";
import type { Summary } from "../../../lib/types";

interface RepoPart {
  title: string;
  tagline: string;
  icon: LucideIcon;
  points: string[];
}

// Facts not in summary.json (tests, coverage) come from the repo's README and CI.
function repoParts(summary: Summary): RepoPart[] {
  const providers = new Set(summary.models.map((model) => model.provider)).size;
  return [
    {
      title: "Compiler",
      tagline: "Python, from scratch, zero runtime dependencies.",
      icon: Cpu,
      points: [
        "490+ tests, 97% coverage, CI on Python 3.10–3.13",
        "Positioned errors with fix-it hints (did you mean 'size'?)",
        "Reports every independent error in one run, without cascades",
        "Sandboxed interpreter with step, depth and output limits",
      ],
    },
    {
      title: "Benchmark",
      tagline: "Models learn MiniLang from its spec, using the compiler as a tool.",
      icon: FlaskConical,
      points: [
        `${summary.models.length} models, ${summary.conditions.length} feedback conditions, ${count(summary.totals.episodes)} graded episodes`,
        `Anthropic, OpenAI Responses and Ollama adapters (${providers} providers)`,
        "Prompt caching and a resumable episode cache",
        "Deterministic grading by exact output",
      ],
    },
    {
      title: "MCP server",
      tagline: "The compiler as tools for AI assistants.",
      icon: Plug,
      points: [
        "run_program, check_program and compile_program tools",
        "The language spec as the minilang://spec resource",
        "Works with Claude Desktop and Claude Code over stdio",
      ],
    },
  ];
}

export function RepoCards({ summary }: { summary: Summary }) {
  return (
    <div className="grid gap-4 md:grid-cols-3">
      {repoParts(summary).map((part) => {
        const Icon = part.icon;
        return (
          <Card key={part.title} className="flex flex-col">
            <span className="grid size-10 place-items-center rounded-xl bg-accent-soft/60 text-accent-ink">
              <Icon className="size-5" aria-hidden />
            </span>
            <h3 className="mt-4 text-lg font-semibold tracking-tight text-ink">{part.title}</h3>
            <p className="mt-1 text-sm text-ink-2">{part.tagline}</p>
            <ul className="mt-4 space-y-2 border-t border-border pt-4 text-sm text-ink-2">
              {part.points.map((point) => (
                <li key={point} className="flex gap-2">
                  <Check className="mt-0.5 size-4 shrink-0 text-good" aria-hidden />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </Card>
        );
      })}
    </div>
  );
}
