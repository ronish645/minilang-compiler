// A tiny MiniLang syntax highlighter. MiniLang has no multi-line strings or
// block comments, so tokenizing one line at a time is exact enough for display.

export type TokenKind = "keyword" | "literal" | "string" | "number" | "comment" | "builtin" | "call" | "plain";

export interface CodeToken {
  kind: TokenKind;
  text: string;
}

const KEYWORDS = new Set([
  "fn", "let", "const", "if", "else", "while", "for", "return", "break", "continue",
]);
const LITERALS = new Set(["true", "false", "null"]);
const BUILTINS = new Set([
  "print", "len", "push", "pop", "str", "int", "abs", "min", "max", "ord", "chr", "slice",
]);

// Order matters: comment, string, number, identifier, then anything else.
const TOKEN_PATTERN = /(\/\/.*)|("(?:[^"\\]|\\.)*"?)|(\d+(?:\.\d+)?)|([A-Za-z_]\w*)|(\s+|[^\sA-Za-z_\d"]+?)/g;

function identifierKind(name: string, rest: string): TokenKind {
  if (KEYWORDS.has(name)) return "keyword";
  if (LITERALS.has(name)) return "literal";
  if (BUILTINS.has(name)) return "builtin";
  return /^\s*\(/.test(rest) ? "call" : "plain";
}

export function tokenizeLine(line: string): CodeToken[] {
  const tokens: CodeToken[] = [];
  for (const match of line.matchAll(TOKEN_PATTERN)) {
    const [text, comment, string, number, ident] = match;
    const end = (match.index ?? 0) + text.length;
    let kind: TokenKind = "plain";
    if (comment) kind = "comment";
    else if (string) kind = "string";
    else if (number) kind = "number";
    else if (ident) kind = identifierKind(ident, line.slice(end));
    const last = tokens[tokens.length - 1];
    // Merge runs of plain text so the DOM stays small.
    if (kind === "plain" && last?.kind === "plain") {
      tokens[tokens.length - 1] = { kind, text: last.text + text };
    } else {
      tokens.push({ kind, text });
    }
  }
  return tokens;
}

export const TOKEN_CLASS: Record<TokenKind, string> = {
  keyword: "text-accent-ink font-medium",
  literal: "text-critical",
  string: "text-good",
  number: "text-critical",
  comment: "text-muted italic",
  builtin: "text-ink font-medium",
  call: "text-ink font-medium",
  plain: "text-ink",
};
