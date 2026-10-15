import { BookOpen, Bot, CircleCheck, MessageSquareText, Play, Repeat, Send, type LucideIcon } from "lucide-react";
import type { Summary } from "../../../lib/types";

interface Step {
  title: string;
  detail: string;
  icon: LucideIcon;
}

const BEFORE: Step = {
  title: "Spec + task",
  detail: "The full language spec in the system prompt; the task and its exact expected output.",
  icon: BookOpen,
};

const LOOP: Step[] = [
  { title: "Model writes code", detail: "A MiniLang program.", icon: Bot },
  { title: "run_minilang", detail: "The compiler runs it as a tool call.", icon: Play },
  { title: "Feedback", detail: "What it sees on failure depends on the condition.", icon: MessageSquareText },
];

const AFTER: Step[] = [
  { title: "submit_solution", detail: "The model decides when it's done.", icon: Send },
  { title: "Graded", detail: "Run the program; printed lines must match exactly.", icon: CircleCheck },
];

function StepItem({ step, index }: { step: Step; index: number }) {
  const Icon = step.icon;
  return (
    <li className="flex gap-3">
      <span className="relative grid size-9 shrink-0 place-items-center rounded-full border border-border bg-surface text-ink-2">
        <Icon className="size-4" aria-hidden />
        <span className="absolute -right-1 -top-1 grid size-4 place-items-center rounded-full bg-accent text-[10px] font-semibold text-white">
          {index}
        </span>
      </span>
      <div className="min-w-0 pt-0.5">
        <p className={step.title.includes("_") ? "font-mono text-sm font-semibold text-ink" : "text-sm font-semibold text-ink"}>
          {step.title}
        </p>
        <p className="text-sm text-ink-2">{step.detail}</p>
      </div>
    </li>
  );
}

/** The agent loop as a compact step diagram, plus what each condition shows. */
export function EpisodeFlow({ summary }: { summary: Summary }) {
  return (
    <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
      <ol className="flex flex-col gap-5 rounded-2xl border border-border bg-surface p-5 sm:p-6">
        <StepItem step={BEFORE} index={1} />
        <li className="rounded-xl border border-dashed border-accent/50 bg-accent-soft/15 p-4">
          <p className="mb-4 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-accent-ink">
            <Repeat className="size-3.5" aria-hidden />
            Loop · up to 5 runs
          </p>
          <ol className="flex flex-col gap-4">
            {LOOP.map((step, i) => (
              <StepItem key={step.title} step={step} index={i + 2} />
            ))}
          </ol>
        </li>
        {AFTER.map((step, i) => (
          <StepItem key={step.title} step={step} index={i + 2 + LOOP.length} />
        ))}
      </ol>

      <div className="rounded-2xl border border-border bg-surface p-5 sm:p-6">
        <h3 className="text-base font-semibold tracking-tight text-ink">The feedback conditions</h3>
        <p className="mt-1 text-sm text-ink-2">
          The experimental variable: only the failure message changes. Successful runs look the same in every condition.
        </p>
        <dl className="mt-4 divide-y divide-border">
          {summary.conditions.map((condition) => (
            <div key={condition.id} className="grid gap-1 py-3 sm:grid-cols-[7rem_1fr] sm:gap-4">
              <dt className="font-mono text-sm font-medium text-ink">{condition.id}</dt>
              <dd className="text-sm text-ink-2">{condition.description}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}
