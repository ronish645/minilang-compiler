import type { ReactNode } from "react";

// Subtle coloring for TAC and stack-machine assembly: temps (t1), labels,
// opcodes/keywords, string and number literals.
const TOKEN = /('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|\bt\d+\b|\b[A-Z][A-Z_]*\d+\b|\b\d+(?:\.\d+)?\b)/g;

const OPS = new Set([
  "func", "endfunc", "param", "call", "return", "print", "label", "goto", "if_false", "if_true",
]);

function tokenClass(part: string): string {
  if (part.startsWith("'") || part.startsWith('"')) return "text-good";
  if (/^t\d+$/.test(part)) return "text-accent-ink font-medium";
  if (/^\d/.test(part)) return "text-series-2";
  return "text-series-5"; // a label
}

function colorize(line: string): ReactNode[] {
  const [first, ...rest] = line.split(" ");
  const isOp = OPS.has(first) || /^[A-Z_]+$/.test(first);
  const tail = (isOp ? rest.join(" ") : line).split(TOKEN);
  const nodes: ReactNode[] = [];
  if (isOp) nodes.push(<span key="op" className="text-ink-2 font-semibold">{first}</span>, rest.length ? " " : "");
  tail.forEach((part, i) => {
    if (!part) return;
    nodes.push(i % 2 === 1 ? <span key={i} className={tokenClass(part)}>{part}</span> : part);
  });
  return nodes;
}

interface CodeListingProps {
  lines: string[];
  label: string;
  caption: string;
}

/** A numbered, lightly highlighted listing (TAC or assembly). */
export function CodeListing({ lines, label, caption }: CodeListingProps) {
  return (
    <div>
      <p className="mb-2 text-xs text-muted">
        {lines.length} instructions · {caption}
      </p>
      <div className="max-h-[520px] overflow-auto lg:max-h-none rounded-xl border border-border bg-code py-2">
        <ol aria-label={label} className="font-mono text-[12.5px] leading-[1.7]">
          {lines.map((line, i) => {
            const structural = /^(func|endfunc|FUNC|END_FUNC|label|LABEL)\b/.test(line);
            return (
              <li key={i} className={structural ? "flex bg-surface-2/60" : "flex"}>
                <span aria-hidden className="w-12 shrink-0 select-none pr-3 text-right tabular-nums text-muted">
                  {i + 1}
                </span>
                <code className="whitespace-pre pr-4 text-ink">{colorize(line)}</code>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
