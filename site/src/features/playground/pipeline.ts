// The five compiler stages, in order, and helpers that read an ExploreResult.
import type { ExploreResult, Stage, Timings } from "./worker/protocol";

export type StageStatus = "passed" | "failed" | "skipped" | "idle";

export interface PipelineStage {
  key: keyof Timings;
  label: string;
  /** The error stage this step reports (codegen never fails on checked code). */
  errorStage: Stage | null;
  produces: string;
}

export const PIPELINE: PipelineStage[] = [
  { key: "lex", label: "Lexer", errorStage: "lexer", produces: "tokens" },
  { key: "parse", label: "Parser", errorStage: "syntax", produces: "an AST" },
  { key: "check", label: "Type checker", errorStage: "semantic", produces: "a checked AST" },
  { key: "codegen", label: "Codegen", errorStage: null, produces: "TAC and assembly" },
  { key: "run", label: "Interpreter", errorStage: "runtime", produces: "output" },
];

export const STAGE_LABEL: Record<Stage, string> = {
  lexer: "Lexer",
  syntax: "Parser",
  semantic: "Type checker",
  runtime: "Runtime",
};

export function stageStatus(result: ExploreResult | null, stage: PipelineStage): StageStatus {
  if (!result) return "idle";
  if (result.timings_ms[stage.key] === undefined) return "skipped";
  return stage.errorStage !== null && result.failed_stage === stage.errorStage ? "failed" : "passed";
}

/** "0.42 ms" / "12.3 ms": enough precision to compare stages without noise. */
export function formatMs(ms: number | undefined): string {
  if (ms === undefined) return "—";
  return ms < 10 ? `${ms.toFixed(2)} ms` : `${ms.toFixed(1)} ms`;
}

export function totalMs(result: ExploreResult): number {
  return Object.values(result.timings_ms).reduce((sum, ms) => sum + (ms ?? 0), 0);
}

const FAILED_PHRASE: Record<Stage, string> = {
  lexer: "The lexer hit an error",
  syntax: "Parsing failed",
  semantic: "Type checking failed",
  runtime: "The program hit a runtime error",
};

/** Why a stage's artifact is missing, in one friendly sentence. */
export function whyMissing(result: ExploreResult, artifact: string): string {
  const failed = result.failed_stage;
  if (!failed) return `No ${artifact} for this program.`;
  return `${FAILED_PHRASE[failed]}, so there's no ${artifact}. Fix the error and it will appear here.`;
}
