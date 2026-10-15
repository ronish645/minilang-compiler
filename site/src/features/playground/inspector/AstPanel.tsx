import { ChevronsDownUp, ChevronsUpDown } from "lucide-react";
import { useMemo, useState } from "react";
import { Button } from "../../../components/ui/Button";
import type { AstNode } from "../worker/protocol";
import { AstTreeNode, type ExpandMode } from "./AstTree";

const countNodes = (node: AstNode): number =>
  1 + node.children.reduce((sum, child) => sum + countNodes(child), 0);

/** The parser's tree, collapsible, with expand/collapse all. */
export function AstPanel({ ast }: { ast: AstNode }) {
  // Changing the key remounts the tree so every node re-reads the mode.
  const [view, setView] = useState<{ mode: ExpandMode; key: number }>({ mode: "default", key: 0 });
  const total = useMemo(() => countNodes(ast), [ast]);
  const apply = (mode: ExpandMode) => setView((v) => ({ mode, key: v.key + 1 }));

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted">{total} nodes · literal types shown as badges</p>
        <div className="flex gap-1">
          <Button size="sm" variant="ghost" icon={<ChevronsUpDown className="size-3.5" />} onClick={() => apply("all")}>
            Expand all
          </Button>
          <Button size="sm" variant="ghost" icon={<ChevronsDownUp className="size-3.5" />} onClick={() => apply("none")}>
            Collapse all
          </Button>
        </div>
      </div>
      <div className="max-h-[520px] overflow-auto lg:max-h-none rounded-xl border border-border bg-surface p-1.5">
        <ul aria-label="Abstract syntax tree" key={view.key}>
          <AstTreeNode node={ast} depth={0} mode={view.mode} />
        </ul>
      </div>
    </div>
  );
}
