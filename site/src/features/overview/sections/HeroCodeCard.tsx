import { Check, ChevronRight } from "lucide-react";
import { MiniLangCode } from "../code/MiniLangCode";
import { HERO_FILENAME, HERO_OUTPUT, HERO_PROGRAM } from "../heroProgram";

const STAGES = ["lex", "parse", "check", "codegen", "run"];

/** An editor-style card: a real MiniLang program, then its output like a terminal. */
export function HeroCodeCard() {
  return (
    <figure className="relative">
      <div
        aria-hidden
        className="absolute -inset-4 -z-10 rounded-[2rem] bg-accent-soft/25 blur-2xl"
      />
      <div className="overflow-hidden rounded-2xl border border-border-strong bg-surface shadow-xl shadow-black/5">
        <div className="flex items-center gap-3 border-b border-border bg-surface-2 px-4 py-2.5">
          <span aria-hidden className="flex gap-1.5">
            <span className="size-2.5 rounded-full bg-surface-3 ring-1 ring-border-strong" />
            <span className="size-2.5 rounded-full bg-surface-3 ring-1 ring-border-strong" />
            <span className="size-2.5 rounded-full bg-surface-3 ring-1 ring-border-strong" />
          </span>
          <span className="font-mono text-xs text-ink-2">{HERO_FILENAME}</span>
        </div>

        <MiniLangCode
          code={HERO_PROGRAM}
          lineNumbers
          label="Example MiniLang program using closures"
          className="bg-code px-4 py-4"
        />

        <div className="border-t border-border bg-surface px-4 py-3 font-mono text-[13px] leading-6">
          <p className="flex items-center gap-1 text-muted">
            <ChevronRight className="size-3.5" aria-hidden />
            minilang run {HERO_FILENAME}
          </p>
          {HERO_OUTPUT.map((line) => (
            <p key={line} className="pl-[1.125rem] text-ink">
              {line}
            </p>
          ))}
        </div>

        <figcaption className="flex flex-wrap items-center justify-between gap-2 border-t border-border bg-surface-2 px-4 py-2 text-xs">
          <span className="inline-flex items-center gap-1.5 font-medium text-good">
            <Check className="size-3.5" aria-hidden />
            compiled · {STAGES.length} stages
          </span>
          <span className="font-mono text-muted">{STAGES.join(" → ")}</span>
        </figcaption>
      </div>
    </figure>
  );
}
