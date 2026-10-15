import { Binary, FileCode2, ListTree, Rows3, SquareTerminal } from "lucide-react";
import type { ReactNode } from "react";
import { Tabs, type TabItem } from "../../../components/ui/Tabs";
import { cn } from "../../../lib/cn";
import { whyMissing } from "../pipeline";
import type { ExploreResult, Token } from "../worker/protocol";
import { AstPanel } from "./AstPanel";
import { CodeListing } from "./CodeListing";
import { EmptyStage } from "./EmptyStage";
import { OutputPanel } from "./OutputPanel";
import { TokensPanel } from "./TokensPanel";

export type InspectorTab = "output" | "tokens" | "ast" | "tac" | "asm";

function CountBadge({ value, tone = "neutral" }: { value: number; tone?: "neutral" | "critical" }) {
  return (
    <span
      className={cn(
        "rounded-full px-1.5 text-[11px] tabular-nums",
        tone === "critical" ? "bg-critical/15 text-critical" : "bg-surface-2 text-muted",
      )}
    >
      {value}
    </span>
  );
}

function buildTabs(result: ExploreResult): TabItem<InspectorTab>[] {
  const icon = (node: ReactNode) => <span className="text-muted">{node}</span>;
  const errors = result.errors.length;
  return [
    {
      id: "output",
      label: "Output",
      icon: icon(<SquareTerminal className="size-3.5" aria-hidden />),
      badge: errors > 0 ? <CountBadge value={errors} tone="critical" /> : undefined,
    },
    {
      id: "tokens",
      label: "Tokens",
      icon: icon(<Rows3 className="size-3.5" aria-hidden />),
      badge: result.tokens ? <CountBadge value={result.tokens.length} /> : undefined,
    },
    { id: "ast", label: "AST", icon: icon(<ListTree className="size-3.5" aria-hidden />) },
    { id: "tac", label: "TAC", icon: icon(<FileCode2 className="size-3.5" aria-hidden />) },
    { id: "asm", label: "Assembly", icon: icon(<Binary className="size-3.5" aria-hidden />) },
  ];
}

interface InspectorProps {
  result: ExploreResult;
  tab: InspectorTab;
  onTabChange: (tab: InspectorTab) => void;
  onHoverToken: (token: Token | null) => void;
}

function Panel({ result, tab, onHoverToken }: Omit<InspectorProps, "onTabChange">) {
  switch (tab) {
    case "output":
      return <OutputPanel result={result} />;
    case "tokens":
      return result.tokens ? (
        <TokensPanel tokens={result.tokens} onHover={onHoverToken} />
      ) : (
        <EmptyStage message={whyMissing(result, "token list")} />
      );
    case "ast":
      return result.ast ? <AstPanel ast={result.ast} /> : <EmptyStage message={whyMissing(result, "AST")} />;
    case "tac":
      return result.tac ? (
        <CodeListing lines={result.tac} label="Three-address code" caption="three-address code: at most one operator per line, temporaries t1, t2, …" />
      ) : (
        <EmptyStage message={whyMissing(result, "generated code")} />
      );
    case "asm":
      return result.asm ? (
        <CodeListing lines={result.asm} label="Assembly" caption="stack-style pseudo-assembly, emitted alongside the TAC" />
      ) : (
        <EmptyStage message={whyMissing(result, "generated code")} />
      );
  }
}

/** Tabs over every artifact the compiler produced for the current program. */
export function Inspector({ result, tab, onTabChange, onHoverToken }: InspectorProps) {
  const tabs = buildTabs(result);
  const label = tabs.find((t) => t.id === tab)?.label ?? tab;
  return (
    <div>
      <Tabs tabs={tabs} active={tab} onChange={onTabChange} label="Compiler stages" />
      <div role="tabpanel" aria-label={label} className="pt-4">
        <Panel result={result} tab={tab} onHoverToken={onHoverToken} />
      </div>
    </div>
  );
}
