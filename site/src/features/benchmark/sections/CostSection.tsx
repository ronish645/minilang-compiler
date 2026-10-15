import { ModelChip } from "../../../components/ui/ModelChip";
import { fraction, pct, usd } from "../../../lib/format";
import { modelColor, modelShort } from "../../../lib/models";
import type { ModelStats } from "../../../lib/types";
import { BarList, type BarRow } from "../chart/BarList";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { TipBody } from "../chart/Tooltip";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { isLocalModel, splitHosted, statsForRun } from "../lib/derive";
import type { SectionProps } from "../lib/sections";

// Per-solve costs are fractions of a cent, so the chart shows cost per 1,000
// solved tasks: same ratios, readable numbers.
const PER = 1000;
const perThousand = (row: ModelStats) => (row.cost_per_solve ?? 0) * PER;

function takeawayFor({ summary, runId }: SectionProps) {
  const { hosted, local } = splitHosted(summary, statsForRun(summary, runId));
  const priced = hosted.filter((row) => row.cost_per_solve != null).sort((a, b) => perThousand(a) - perThousand(b));
  const cheapest = priced[0];
  const priciest = priced[priced.length - 1];
  const localRow = local[0];
  if (!cheapest || !priciest || cheapest === priciest) return "";
  const ratio = Math.round(perThousand(priciest) / perThousand(cheapest));

  return (
    <>
      {modelShort(cheapest.model)} cost {usd(perThousand(cheapest))} per 1,000 solved tasks and passed{" "}
      {pct(cheapest.pass.value)}. {modelShort(priciest.model)} cost {usd(perThousand(priciest))}, about{" "}
      {ratio}× more, and passed {pct(priciest.pass.value)}.{" "}
      {(cheapest.pass.value ?? 0) >= (priciest.pass.value ?? 0) && "The cheapest models were the best value. "}
      {localRow &&
        `${modelShort(localRow.model)} is free to run on a laptop but solved only ${fraction(localRow.pass.hits, localRow.pass.total)}.`}
    </>
  );
}

function barRows(summary: SectionProps["summary"], stats: ModelStats[]): BarRow[] {
  const hosted = stats.filter((row) => !isLocalModel(summary, row.model));
  const max = Math.max(...hosted.map(perThousand), 0);
  const sorted = [...hosted].sort((a, b) => perThousand(a) - perThousand(b));
  const local = stats.filter((row) => isLocalModel(summary, row.model));

  return [...sorted, ...local].map((row) => {
    const free = isLocalModel(summary, row.model);
    const cost = free ? "Free" : `${usd(perThousand(row))} per 1K solves`;
    return {
      key: row.model,
      label: <ModelChip model={row.model} />,
      share: free || max === 0 ? null : perThousand(row) / max,
      note: `Free, runs locally · ${pct(row.pass.value)} passed (${fraction(row.pass.hits, row.pass.total)})`,
      color: modelColor(row.model),
      value: `${usd(perThousand(row))} · ${pct(row.pass.value)} pass`,
      tip: (
        <TipBody
          keyColor={modelColor(row.model)}
          value={cost}
          label={`${modelShort(row.model)} · ${pct(row.pass.value)} passed`}
          detail={`Run total ${usd(row.cost_usd)} for ${row.pass.hits} solves`}
        />
      ),
      ariaLabel: `${modelShort(row.model)}: ${cost}, ${pct(row.pass.value)} passed`,
    };
  });
}

export function CostSection({ summary, runId }: SectionProps) {
  const stats = statsForRun(summary, runId);

  const columns: Column<ModelStats>[] = [
    { key: "model", header: "Model", render: (row) => modelShort(row.model) },
    { key: "per", header: "Cost per solve", numeric: true, render: (row) => usd(row.cost_per_solve) },
    { key: "per1k", header: "Per 1,000 solves", numeric: true, render: (row) => usd(perThousand(row)) },
    { key: "total", header: "Run cost", numeric: true, render: (row) => usd(row.cost_usd) },
    { key: "solves", header: "Solved", numeric: true, render: (row) => fraction(row.pass.hits, row.pass.total) },
    { key: "pass", header: "Pass rate", numeric: true, render: (row) => pct(row.pass.value) },
    { key: "secs", header: "Avg time", numeric: true, render: (row) => `${row.avg_seconds.toFixed(1)}s` },
  ];

  return (
    <BenchmarkSection id="cost" eyebrow="Cost" title="What did a solved task cost?" takeaway={takeawayFor({ summary, runId })}>
      <ChartCard
        title="Cost per 1,000 solved tasks"
        subtitle="Total API spend divided by tasks solved, from token usage with prompt-cache pricing. Sorted cheapest first."
        table={<DataTable caption="Cost per solve by model" columns={columns} rows={stats} rowKey={(r) => r.model} />}
        howToRead={
          <>
            Shorter bars are cheaper. Each label pairs the cost with the pass rate, because a cheap model
            that rarely solves anything isn't good value. The local model has no API bill, so it gets a note
            instead of a bar.
          </>
        }
      >
        <BarList rows={barRows(summary, stats)} valueWidth="w-32" />
      </ChartCard>
    </BenchmarkSection>
  );
}
