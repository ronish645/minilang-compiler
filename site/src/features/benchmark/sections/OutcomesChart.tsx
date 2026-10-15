import { ModelChip } from "../../../components/ui/ModelChip";
import { cn } from "../../../lib/cn";
import { pct } from "../../../lib/format";
import { modelShort } from "../../../lib/models";
import type { ModelStats } from "../../../lib/types";
import { TipBody, TooltipLayer, useTip } from "../chart/Tooltip";
import { OUTCOME_STYLES, outcomeCount } from "../lib/outcomes";

function OutcomeBar({ row }: { row: ModelStats }) {
  const tip = useTip();
  const segments = OUTCOME_STYLES.map((style) => ({ style, n: outcomeCount(row.outcomes, style) })).filter(
    (segment) => segment.n > 0,
  );
  const total = segments.reduce((sum, segment) => sum + segment.n, 0);

  return (
    <div className="flex h-4 min-w-0 flex-1 gap-[2px]">
      {segments.map(({ style, n }, index) => {
        const share = total ? n / total : 0;
        const isLast = index === segments.length - 1;
        return (
          <div
            key={style.key}
            className={cn(
              "h-full min-w-[3px] outline-none transition hover:brightness-110",
              "focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-1 focus-visible:ring-offset-surface",
              isLast && "rounded-r",
            )}
            style={{ flex: `${n} 1 0%`, background: style.color }}
            {...tip.bind(
              <TipBody
                keyColor={style.color}
                value={`${n} of ${total} · ${pct(share)}`}
                label={`${style.label} · ${modelShort(row.model)}`}
              />,
              `${modelShort(row.model)}: ${style.label}, ${n} of ${total} episodes (${pct(share)})`,
            )}
          />
        );
      })}
    </div>
  );
}

/** One 100%-stacked bar per model; the passed share is labelled at the bar end. */
export function OutcomesChart({ stats }: { stats: ModelStats[] }) {
  return (
    <TooltipLayer>
      <ul className="flex flex-col gap-3">
        {stats.map((row) => (
          <li
            key={row.model}
            className="grid grid-cols-1 items-center gap-x-4 gap-y-1.5 sm:grid-cols-[8.5rem_minmax(0,1fr)_5.5rem]"
          >
            <ModelChip model={row.model} />
            <div className="flex items-center gap-3">
              <OutcomeBar row={row} />
              <span className="w-20 shrink-0 text-right text-xs tabular-nums text-ink-2 sm:hidden">
                {pct(row.pass.value)} passed
              </span>
            </div>
            <span className="hidden text-right text-xs tabular-nums text-ink-2 sm:block">
              {pct(row.pass.value)} passed
            </span>
          </li>
        ))}
      </ul>
    </TooltipLayer>
  );
}
