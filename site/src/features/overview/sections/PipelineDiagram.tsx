import { ArrowRight, Binary, Cpu, FileCode, Network, Play, ShieldCheck, type LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import { cn } from "../../../lib/cn";

interface Stage {
  name: string;
  artifact: string;
  description: string;
  icon: LucideIcon;
}

const STAGES: Stage[] = [
  { name: "Source", artifact: ".ml text", description: "A C/JS-style program.", icon: FileCode },
  { name: "Lexer", artifact: "tokens", description: "Characters to tokens, with line and column.", icon: Binary },
  { name: "Parser", artifact: "AST", description: "Recursive descent; recovers to report many errors.", icon: Network },
  { name: "Type checker", artifact: "gradual types", description: "Scopes, arity and types before anything runs.", icon: ShieldCheck },
];

const BACKENDS: Stage[] = [
  { name: "Codegen", artifact: "TAC", description: "Three-address code and pseudo-assembly.", icon: Cpu },
  { name: "Interpreter", artifact: "sandboxed", description: "Runs it with step, depth and output limits.", icon: Play },
];

/** Keyframes for the moving pulse; hidden entirely when reduced motion is on. */
const FLOW_CSS = `
@keyframes ml-flow-x { from { left: 0%; } to { left: 100%; } }
@keyframes ml-flow-y { from { top: 0%; } to { top: 100%; } }
`;

function Connector({ delay }: { delay: number }) {
  const pulse = "absolute size-1.5 rounded-full bg-accent motion-reduce:hidden";
  return (
    <div aria-hidden className="relative flex shrink-0 items-center justify-center xl:w-8">
      {/* vertical on phones, horizontal on desktop */}
      <div className="relative h-6 w-px bg-border-strong xl:h-px xl:w-full">
        <span
          className={cn(pulse, "-left-[2.5px] xl:hidden")}
          style={{ animation: `ml-flow-y 2.4s ${delay}s linear infinite` }}
        />
        <span
          className={cn(pulse, "-top-[2.5px] hidden xl:block")}
          style={{ animation: `ml-flow-x 2.4s ${delay}s linear infinite` }}
        />
      </div>
    </div>
  );
}

function StageNode({ stage, className }: { stage: Stage; className?: string }) {
  const Icon = stage.icon;
  return (
    <div className={cn("rounded-xl border border-border bg-surface p-4 shadow-sm", className)}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-2 font-semibold text-ink">
          <span className="grid size-7 place-items-center rounded-lg bg-accent-soft/60 text-accent-ink">
            <Icon className="size-4" aria-hidden />
          </span>
          {stage.name}
        </span>
        <span className="rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-[11px] text-ink-2">
          {stage.artifact}
        </span>
      </div>
      <p className="mt-2 text-sm leading-snug text-ink-2">{stage.description}</p>
    </div>
  );
}

export function PipelineDiagram() {
  return (
    <div>
      <style>{FLOW_CSS}</style>
      <ol aria-label="Compiler pipeline" className="flex flex-col items-stretch xl:flex-row">
        {STAGES.map((stage, index) => (
          <li key={stage.name} className="flex flex-col items-stretch xl:flex-1 xl:flex-row">
            <StageNode stage={stage} className="xl:flex-1" />
            <Connector delay={index * 0.3} />
          </li>
        ))}
        <li className="flex flex-col justify-center gap-3 xl:flex-1">
          {BACKENDS.map((stage) => (
            <StageNode key={stage.name} stage={stage} />
          ))}
        </li>
      </ol>
      <Link
        to="/playground"
        className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-accent-ink hover:underline underline-offset-4"
      >
        See every stage live in the playground
        <ArrowRight className="size-4" aria-hidden />
      </Link>
    </div>
  );
}
