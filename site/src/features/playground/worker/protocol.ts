// The typed contract between the page and the compiler Web Worker.
// Both sides import these types, so a renamed field is a compile error,
// not a silent runtime bug.

/** The compiler stage that raised an error (matches MiniLangError.stage). */
export type Stage = "lexer" | "syntax" | "semantic" | "runtime";

export interface Token {
  type: string;
  value: string;
  line: number;
  col: number;
}

export interface AstNode {
  kind: string;
  value: string | number | boolean | null;
  type: string | null;
  line: number;
  col: number;
  children: AstNode[];
}

export interface CompileError {
  stage: Stage;
  message: string;
  line: number;
  col: number;
  hint: string | null;
}

export interface Timings {
  lex?: number;
  parse?: number;
  check?: number;
  codegen?: number;
  run?: number;
}

/** What minilang.playground.explore() returns, as JSON. */
export interface ExploreResult {
  ok: boolean;
  failed_stage: Stage | null;
  tokens: Token[] | null;
  ast: AstNode | null;
  tac: string[] | null;
  asm: string[] | null;
  output: string[];
  errors: CompileError[];
  diagnostic: string | null;
  timings_ms: Timings;
}

/** Page -> worker. `id` pairs each result with the request that asked for it. */
export type WorkerRequest = { type: "explore"; id: number; source: string };

/** Worker -> page. */
export type WorkerResponse =
  | { type: "progress"; message: string }
  | { type: "ready"; pythonVersion: string }
  | { type: "result"; id: number; result: ExploreResult }
  | { type: "error"; id: number | null; message: string };
