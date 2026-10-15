import { ChevronRight } from "lucide-react";
import { useState } from "react";
import { cn } from "../../../lib/cn";
import type { AstNode } from "../worker/protocol";

/** How deep the tree starts open when no "expand/collapse all" was chosen. */
const DEFAULT_OPEN_DEPTH = 2;

export type ExpandMode = "default" | "all" | "none";

interface AstTreeNodeProps {
  node: AstNode;
  depth: number;
  mode: ExpandMode;
}

function initiallyOpen(mode: ExpandMode, depth: number) {
  if (mode === "all") return true;
  if (mode === "none") return depth === 0;
  return depth < DEFAULT_OPEN_DEPTH;
}

function NodeLabel({ node }: { node: AstNode }) {
  return (
    <>
      <span className="font-mono text-[13px] font-medium text-accent-ink">{node.kind}</span>
      {node.value !== null && (
        <span className="truncate font-mono text-[13px] text-ink">
          {node.type === "string" ? JSON.stringify(node.value) : String(node.value)}
        </span>
      )}
      {node.type && (
        <span className="rounded bg-surface-3 px-1.5 py-px font-mono text-[10.5px] text-ink-2">
          {node.type}
        </span>
      )}
      <span className="ml-auto shrink-0 pl-2 font-mono text-[11px] tabular-nums text-muted">
        {node.line}:{node.col}
      </span>
    </>
  );
}

export function AstTreeNode({ node, depth, mode }: AstTreeNodeProps) {
  const [open, setOpen] = useState(() => initiallyOpen(mode, depth));
  const hasChildren = node.children.length > 0;
  const rowClass = "flex w-full min-w-0 items-center gap-2 rounded-md py-1 pr-2 text-left";

  return (
    <li>
      {hasChildren ? (
        <button
          type="button"
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
          className={cn(rowClass, "hover:bg-surface-2")}
          style={{ paddingLeft: depth * 16 + 4 }}
        >
          <ChevronRight
            aria-hidden
            className={cn("size-3.5 shrink-0 text-muted transition-transform", open && "rotate-90")}
          />
          <NodeLabel node={node} />
        </button>
      ) : (
        <div className={rowClass} style={{ paddingLeft: depth * 16 + 4 + 22 }}>
          <NodeLabel node={node} />
        </div>
      )}
      {hasChildren && open && (
        <ul className="relative">
          <span
            aria-hidden
            className="absolute bottom-1 top-0 w-px bg-border"
            style={{ left: depth * 16 + 10 }}
          />
          {node.children.map((child, i) => (
            <AstTreeNode key={i} node={child} depth={depth + 1} mode={mode} />
          ))}
        </ul>
      )}
    </li>
  );
}
