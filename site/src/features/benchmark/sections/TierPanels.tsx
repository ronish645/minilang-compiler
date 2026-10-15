import { ModelChip } from "../../../components/ui/ModelChip";
import { fraction, pct } from "../../../lib/format";
import { modelColor, modelShort } from "../../../lib/models";
import type { TierRow } from "../../../lib/types";
import { TipBody, TooltipLayer, useTip } from "../chart/Tooltip";

const GRID = [0, 0.5, 1];
// Full columns read off the labelled 100% gridline; only columns below it get a
// cap label (selective labels: the exceptions are the story).
const PLOT_HEIGHT = "h-28"; // 112px plot; the axis band sits below it, inside the panel

function Panel({ model, rows }: { model: string; rows: TierRow[] }) {
  const tip = useTip();
  return (
    <figure className="rounded-xl border border-border p-3">
      <figcaption className="mb-3">
        <ModelChip model={model} />
      </figcaption>
      <div className={`${PLOT_HEIGHT} pt-5`}>
        <div className="relative flex h-full items-end justify-around gap-[2px] pl-7">
          {GRID.map((line) => (
            <span
              key={line}
              aria-hidden
              className={line === 0 ? "absolute inset-x-0 h-px bg-axis" : "absolute inset-x-0 h-px bg-grid"}
              style={{ bottom: `${line * 100}%` }}
            >
              {line > 0 && (
                <span className="absolute -top-1.5 left-0 bg-surface pr-1 text-[10px] leading-3 tabular-nums text-muted">{pct(line)}</span>
              )}
            </span>
          ))}
          {rows.map((row) => {
            const value = row.pass.value ?? 0;
            const label = `${modelShort(model)}, tier ${row.tier}: ${pct(value)} (${fraction(row.pass.hits, row.pass.total)})`;
            return (
              <div
                key={row.tier}
                className="relative flex h-full w-6 flex-col items-center justify-end rounded-t outline-none focus-visible:ring-2 focus-visible:ring-accent"
                {...tip.bind(
                  <TipBody
                    keyColor={modelColor(model)}
                    value={`${pct(value)} · ${fraction(row.pass.hits, row.pass.total)}`}
                    label={`${modelShort(model)} · tier ${row.tier}`}
                  />,
                  label,
                )}
              >
                {value < 1 && (
                  <span className="mb-0.5 shrink-0 whitespace-nowrap text-[10px] tabular-nums text-ink-2">{pct(value)}</span>
                )}
                <span
                  aria-hidden
                  className="block w-full shrink-0 rounded-t transition hover:brightness-110"
                  style={{ height: `${Math.max(value * 100, 1)}%`, background: modelColor(model) }}
                />
              </div>
            );
          })}
        </div>
      </div>
      <div aria-hidden className="mt-1.5 flex justify-around gap-[2px] pl-7 text-[11px] tabular-nums text-muted">
        {rows.map((row) => (
          <span key={row.tier} className="w-6 text-center">
            T{row.tier}
          </span>
        ))}
      </div>
    </figure>
  );
}

/** Small multiples: one panel per model, one column per tier, a shared 0–100% scale. */
export function TierPanels({ models, rows }: { models: string[]; rows: TierRow[] }) {
  return (
    <TooltipLayer>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-5">
        {models.map((model) => (
          <Panel
            key={model}
            model={model}
            rows={rows.filter((row) => row.model === model).sort((a, b) => a.tier - b.tier)}
          />
        ))}
      </div>
    </TooltipLayer>
  );
}
