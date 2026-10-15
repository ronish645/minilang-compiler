import { ArrowDown, ArrowRight, Bot, CircleCheck, FileText, RotateCcw, Send, Terminal, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

interface StepProps {
  icon: LucideIcon;
  title: string;
  children: ReactNode;
}

function Step({ icon: Icon, title, children }: StepProps) {
  return (
    <div className="flex min-w-0 flex-1 basis-0 flex-col rounded-xl border border-border bg-surface p-3">
      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
        <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-surface-2 text-ink-2">
          <Icon aria-hidden className="size-4" />
        </span>
        {title}
      </div>
      <div className="mt-2 text-xs leading-relaxed text-ink-2">{children}</div>
    </div>
  );
}

function Arrow({ turn = false }: { turn?: boolean }) {
  return (
    <div aria-hidden className="grid shrink-0 place-items-center py-0.5 text-muted">
      <ArrowDown className={turn ? "size-4 md:hidden" : "size-4"} />
      {turn && <ArrowRight className="hidden size-4 md:block" />}
    </div>
  );
}

const code = (text: string) => (
  <code className="break-all rounded bg-surface-2 px-1 font-mono text-[11px] text-ink">{text}</code>
);

/** One episode, top to bottom: prompt, the tool loop, submission, grading. */
export function AgentLoopDiagram() {
  return (
    <figure aria-label="How one benchmark episode works" className="mx-auto max-w-3xl">
      <ol className="flex flex-col">
        <li className="flex">
          <Step icon={FileText} title="Spec + task">
            The whole MiniLang spec goes in the system prompt; the task and its exact expected output come
            from the user.
          </Step>
        </li>
        <li aria-hidden>
          <Arrow />
        </li>
        <li className="rounded-2xl bg-surface-2 p-2 ring-1 ring-inset ring-border">
          <p className="flex items-center gap-1.5 px-1 pb-2 text-xs font-medium text-ink-2">
            <RotateCcw aria-hidden className="size-3.5" />
            Tool loop: repeats up to 5 runs and 8 model turns (skipped in one-shot)
          </p>
          <div className="flex flex-col md:flex-row md:items-stretch">
            <Step icon={Bot} title="Model">
              Writes a MiniLang program, then decides: run it, or submit it.
            </Step>
            <Arrow turn />
            <Step icon={Terminal} title="Compiler">
              {code("run_minilang(code)")} compiles and runs the program in a sandbox.
            </Step>
            <Arrow turn />
            <Step icon={RotateCcw} title="Feedback">
              On success, the printed output. On failure, a message whose detail depends on the condition.
            </Step>
          </div>
        </li>
        <li aria-hidden>
          <Arrow />
        </li>
        <li className="flex">
          <Step icon={Send} title="Submit">
            {code("submit_solution(code)")} ends the episode with a final program.
          </Step>
        </li>
        <li aria-hidden>
          <Arrow />
        </li>
        <li className="flex">
          <Step icon={CircleCheck} title="Grade">
            The grader runs the program. It passes only if every printed line matches the expected output
            exactly.
          </Step>
        </li>
      </ol>
      <figcaption className="mt-3 text-xs text-muted">
        One episode = one model × one task × one feedback condition. The reference solution is never shown.
      </figcaption>
    </figure>
  );
}
