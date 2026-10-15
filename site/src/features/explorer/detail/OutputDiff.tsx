import { cn } from "../../../lib/cn";

interface OutputDiffProps {
  output: string[];
  expected: string[];
}

interface ColumnProps {
  title: string;
  lines: string[];
  other: string[];
  emptyText: string;
}

function Column({ title, lines, other, emptyText }: ColumnProps) {
  return (
    <div className="min-w-0 overflow-hidden rounded-xl border border-border">
      <p className="border-b border-border bg-surface-2 px-3 py-1.5 text-xs font-medium text-ink-2">{title}</p>
      {lines.length === 0 ? (
        <p className="bg-code px-3 py-2 text-sm italic text-muted">{emptyText}</p>
      ) : (
        <ol className="overflow-x-auto bg-code py-1 font-mono text-[13px] leading-6">
          {lines.map((line, i) => {
            const mismatch = line !== other[i];
            return (
              <li
                key={i}
                className={cn("flex min-w-max pr-3", mismatch && "bg-critical/10")}
              >
                <span aria-hidden className="w-8 shrink-0 select-none pr-2 text-right text-muted/70">
                  {i + 1}
                </span>
                <span className={cn("whitespace-pre", mismatch ? "text-critical" : "text-ink")}>
                  {line || " "}
                </span>
                {mismatch && <span className="sr-only"> (differs)</span>}
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

/** Printed output next to the expected output; lines that differ are highlighted. */
export function OutputDiff({ output, expected }: OutputDiffProps) {
  const same = output.length === expected.length && output.every((line, i) => line === expected[i]);
  return (
    <div className="space-y-2">
      <p className={cn("text-sm", same ? "text-good" : "text-ink-2")}>
        {same
          ? "Output matches the expected lines exactly."
          : "Highlighted lines differ (compared line by line)."}
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <Column title="Program output" lines={output} other={expected} emptyText="No output" />
        <Column title="Expected" lines={expected} other={output} emptyText="Nothing expected" />
      </div>
    </div>
  );
}
