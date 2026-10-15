import type { ReactNode } from "react";
import { cn } from "../../../lib/cn";
import { TooltipLayer, useTip } from "./Tooltip";

export interface BarRow {
  key: string;
  label: ReactNode;
  share: number | null; // bar length as a share of the track (0–1); null draws no bar
  color: string;
  value: ReactNode; // direct label at the bar end
  tip: ReactNode;
  ariaLabel: string;
  note?: ReactNode; // shown in place of a bar when share is null
}

interface BarListProps {
  rows: BarRow[];
  layout?: "side" | "above"; // label beside the bar, or on its own line above it
  valueWidth?: string; // fixed width for the value column, so every track has the same length
  track?: boolean; // show the 100% track behind each bar (for rates out of a whole)
}

const BAR_HEIGHT = "h-4"; // 16px: thin marks, well under the 24px cap

function Bar({ row, valueWidth, track }: { row: BarRow; valueWidth: string; track: boolean }) {
  const tip = useTip();
  return (
    <div
      className="flex min-w-0 items-center gap-2 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-accent"
      {...tip.bind(row.tip, row.ariaLabel)}
    >
      {row.share == null ? (
        <span className="text-xs text-ink-2">{row.note}</span>
      ) : (
        <>
          <span className={cn("relative min-w-0 flex-1 rounded-r", track && "bg-surface-2")}>
            <span
              aria-hidden
              className={cn("block rounded-r transition hover:brightness-110", BAR_HEIGHT)}
              style={{ width: `${Math.max(row.share * 100, 0.6)}%`, background: row.color }}
            />
          </span>
          <span className={cn("shrink-0 text-xs tabular-nums text-ink-2", valueWidth)}>{row.value}</span>
        </>
      )}
    </div>
  );
}

/** Horizontal bars from a single baseline, each labelled at its end. */
export function BarList({ rows, layout = "side", valueWidth = "w-24", track = false }: BarListProps) {
  return (
    <TooltipLayer>
      <ul className={cn("flex flex-col", layout === "side" ? "gap-3" : "gap-4")}>
        {rows.map((row) => (
          <li
            key={row.key}
            className={cn(
              "grid items-center gap-x-4 gap-y-1",
              layout === "side" ? "grid-cols-1 sm:grid-cols-[8.5rem_minmax(0,1fr)]" : "grid-cols-1",
            )}
          >
            <div className="min-w-0 text-sm text-ink">{row.label}</div>
            <Bar row={row} valueWidth={valueWidth} track={track} />
          </li>
        ))}
      </ul>
    </TooltipLayer>
  );
}
