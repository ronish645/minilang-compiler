import { useEffect } from "react";
import { Badge } from "../../../components/ui/Badge";
import type { Token } from "../worker/protocol";

type Tone = "neutral" | "accent" | "good" | "warning";

const TYPE_TONE: Record<string, Tone> = {
  KW: "accent",
  IDENT: "neutral",
  INT: "warning",
  FLOAT: "warning",
  STRING: "good",
};

interface TokensPanelProps {
  tokens: Token[];
  onHover: (token: Token | null) => void;
}

/** The lexer's output. Hovering a row highlights that token in the editor. */
export function TokensPanel({ tokens, onHover }: TokensPanelProps) {
  // Never leave a highlight behind when the tab closes or the tokens change.
  useEffect(() => () => onHover(null), [tokens, onHover]);
  return (
    <div>
      <p className="mb-2 text-xs text-muted">
        {tokens.length} tokens · hover a row to find it in the editor
      </p>
      <div className="max-h-[520px] overflow-auto lg:max-h-none rounded-xl border border-border">
        <table className="w-full text-left text-sm" onMouseLeave={() => onHover(null)}>
          <thead className="sticky top-0 bg-surface-2 text-xs text-ink-2">
            <tr>
              <th scope="col" className="px-3 py-2 font-medium">#</th>
              <th scope="col" className="px-3 py-2 font-medium">Type</th>
              <th scope="col" className="px-3 py-2 font-medium">Value</th>
              <th scope="col" className="px-3 py-2 text-right font-medium">Line:col</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {tokens.map((token, i) => (
              <tr
                key={i}
                onMouseEnter={() => onHover(token)}
                className="transition-colors hover:bg-accent-soft/40 [&>td]:py-1"
              >
                <td className="px-3 py-1.5 font-mono text-xs tabular-nums text-muted">{i + 1}</td>
                <td className="px-3 py-1.5">
                  <Badge tone={TYPE_TONE[token.type] ?? "neutral"} className="font-mono">
                    {token.type}
                  </Badge>
                </td>
                <td className="max-w-[16rem] truncate px-3 py-1.5 font-mono text-[13px] text-ink">
                  {token.type === "STRING" ? JSON.stringify(token.value) : token.value || <span className="text-muted">∅</span>}
                </td>
                <td className="px-3 py-1.5 text-right font-mono text-xs tabular-nums text-muted">
                  {token.line}:{token.col}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
