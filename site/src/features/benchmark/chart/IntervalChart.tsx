import type { ReactNode } from "react";
import { fraction, pct } from "../../../lib/format";
import { TipBody, TooltipLayer, useTip } from "./Tooltip";

export interface IntervalRow {
  key: string;
  label: ReactNode;
  name: string;
  value: number;
  low: number;
  high: number;
  hits: number;
  total: number;
}

const TICKS = [0, 0.25, 0.5, 0.75, 1];
const at = (value: number) => `${(value * 100).toFixed(2)}%`;

function Gridlines() {
  return (
    <>
      {TICKS.map((tick) => (
        <span key={tick} aria-hidden className="absolute inset-y-0 w-px bg-grid" style={{ left: at(tick) }} />
      ))}
    </>
  );
}

function Row({ row }: { row: IntervalRow }) {
  const tip = useTip();
  const ci = `95% interval ${pct(row.low)}–${pct(row.high)}`;
  return (
    <li
      className="grid grid-cols-[6.5rem_minmax(0,1fr)_3.5rem] items-center gap-x-3 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-accent sm:grid-cols-[8rem_minmax(0,1fr)_4.5rem]"
      {...tip.bind(
        <TipBody value={`${pct(row.value)} repaired`} label={`${row.name} · ${fraction(row.hits, row.total)}`} detail={ci} />,
        `${row.name}: ${pct(row.value)} repaired, ${row.hits} of ${row.total}, ${ci}`,
      )}
    >
      <span className="text-sm text-ink">{row.label}</span>
      <span className="relative h-10">
        <Gridlines />
        <span
          aria-hidden
          className="absolute top-1/2 h-0.5 -translate-y-1/2 rounded-full bg-ink-2"
          style={{ left: at(row.low), width: at(row.high - row.low) }}
        />
        {[row.low, row.high].map((edge, i) => (
          <span
            key={i}
            aria-hidden
            className="absolute top-1/2 h-3 w-0.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink-2"
            style={{ left: at(edge) }}
          />
        ))}
        <span
          aria-hidden
          className="absolute top-1/2 size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-ink ring-2 ring-surface"
          style={{ left: at(row.value) }}
        />
      </span>
      <span className="text-right text-xs tabular-nums text-ink-2">n = {row.total}</span>
    </li>
  );
}

/** Point estimate (dot) with its 95% interval (whisker) on a shared 0–100% axis. */
export function IntervalChart({ rows, axisLabel }: { rows: IntervalRow[]; axisLabel: string }) {
  return (
    <TooltipLayer>
      <ul className="flex flex-col">
        {rows.map((row) => (
          <Row key={row.key} row={row} />
        ))}
      </ul>
      <div
        aria-hidden
        className="grid grid-cols-[6.5rem_minmax(0,1fr)_3.5rem] gap-x-3 sm:grid-cols-[8rem_minmax(0,1fr)_4.5rem]"
      >
        <span />
        <span className="relative h-5 border-t border-axis text-[11px] tabular-nums text-muted">
          {TICKS.map((tick) => (
            <span
              key={tick}
              className="absolute top-1 -translate-x-1/2 first:translate-x-0 last:-translate-x-full"
              style={{ left: at(tick) }}
            >
              {pct(tick)}
            </span>
          ))}
        </span>
      </div>
      <p className="mt-1 text-center text-xs text-muted">{axisLabel}</p>
    </TooltipLayer>
  );
}
