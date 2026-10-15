import { ModelChip } from "../../../components/ui/ModelChip";
import { cn } from "../../../lib/cn";
import { fraction, pct } from "../../../lib/format";
import { modelColor, modelShort } from "../../../lib/models";
import type { Cell, ConditionInfo } from "../../../lib/types";
import { TipBody, TooltipLayer, useTip } from "../chart/Tooltip";
import { seqFill, seqTextClass } from "../lib/sequential";

interface HeatmapChartProps {
  models: string[];
  conditions: ConditionInfo[];
  cellFor: (model: string, condition: string) => Cell | undefined;
}

function Grid({ models, conditions, cellFor }: HeatmapChartProps) {
  const tip = useTip();
  const columns = `minmax(7.5rem, auto) repeat(${conditions.length}, minmax(3.5rem, 1fr))`;

  return (
    <div role="table" aria-label="Pass rate by model and condition" className="min-w-[26rem]">
      <div role="row" className="grid gap-0.5" style={{ gridTemplateColumns: columns }}>
        <div role="columnheader">
          <span className="sr-only">Model</span>
        </div>
        {conditions.map((condition) => (
          <div
            key={condition.id}
            role="columnheader"
            className="flex flex-col items-center justify-end rounded-md px-1 pb-2 text-center outline-none focus-visible:ring-2 focus-visible:ring-accent"
            {...tip.bind(
              <TipBody
                value={condition.label}
                label={condition.description}
                detail={condition.uses_tools ? "Can run code before submitting" : "No tools: one blind attempt"}
              />,
              `${condition.label}: ${condition.description}`,
            )}
          >
            <span className="text-xs font-medium text-ink">{condition.label}</span>
            <span className="text-[11px] text-muted">{condition.uses_tools ? "tools" : "no tools"}</span>
          </div>
        ))}
      </div>

      {models.map((model) => (
        <div key={model} role="row" className="mt-0.5 grid gap-0.5" style={{ gridTemplateColumns: columns }}>
          <div role="rowheader" className="flex items-center pr-3">
            <ModelChip model={model} />
          </div>
          {conditions.map((condition) => {
            const rate = cellFor(model, condition.id)?.pass;
            if (!rate || rate.value == null) {
              return (
                <div key={condition.id} role="cell" className="grid h-11 place-items-center rounded-md bg-surface-2 text-xs text-muted">
                  –
                </div>
              );
            }
            const label = `${modelShort(model)}, ${condition.label}: ${pct(rate.value)} (${fraction(rate.hits, rate.total)} passed)`;
            return (
              <div
                key={condition.id}
                role="cell"
                className={cn(
                  "grid h-11 place-items-center rounded-md text-sm font-semibold tabular-nums outline-none transition",
                  "hover:brightness-110 focus-visible:ring-2 focus-visible:ring-ink focus-visible:ring-offset-2 focus-visible:ring-offset-surface",
                  seqTextClass(rate.value),
                )}
                style={{ background: seqFill(rate.value) }}
                {...tip.bind(
                  <TipBody
                    keyColor={modelColor(model)}
                    value={`${pct(rate.value)} · ${fraction(rate.hits, rate.total)} passed`}
                    label={`${modelShort(model)} · ${condition.label}`}
                  />,
                  label,
                )}
              >
                {pct(rate.value)}
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

/** Models × conditions, shaded on the sequential ramp; every cell is labelled. */
export function HeatmapChart(props: HeatmapChartProps) {
  return (
    <TooltipLayer>
      <div className="overflow-x-auto pb-1">
        <Grid {...props} />
      </div>
    </TooltipLayer>
  );
}
