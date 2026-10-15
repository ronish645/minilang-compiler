import { fraction, pct } from "../../../lib/format";
import { modelShort } from "../../../lib/models";
import type { RepairRow } from "../../../lib/types";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { IntervalChart, type IntervalRow } from "../chart/IntervalChart";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { conditionsForRun, findCell, modelsForRun, poolRates, splitHosted, statsForRun } from "../lib/derive";
import type { SectionProps } from "../lib/sections";

function repairRows({ summary, runId }: SectionProps): RepairRow[] {
  const order = conditionsForRun(summary, runId).map((c) => c.id);
  return summary.repair
    .filter((row) => row.run === runId)
    .sort((a, b) => order.indexOf(a.condition) - order.indexOf(b.condition));
}

function takeawayFor(props: SectionProps, rows: RepairRow[]) {
  const { hosted, local } = splitHosted(props.summary, statsForRun(props.summary, props.runId));
  const hostedRepair = poolRates(hosted.map((row) => row.repair));
  const localRepair = poolRates(local.map((row) => row.repair));
  const localName = local.map((row) => modelShort(row.model)).join(", ");
  const rated = rows.filter((row) => row.rate.value != null && row.rate.low != null && row.rate.high != null);
  const overlap =
    rated.length > 1 &&
    Math.max(...rated.map((row) => row.rate.low ?? 0)) <= Math.min(...rated.map((row) => row.rate.high ?? 1));
  const sizes = rated.map((row) => row.rate.total);
  const values = rated.map((row) => row.rate.value ?? 0);

  const pooled = poolRates(rated.map((row) => row.rate));
  const sizeRange = `${Math.min(...sizes)}–${Math.max(...sizes)}`;
  const flat = values.length > 0 && Math.min(...values) === Math.max(...values);
  const headline = flat
    ? `Every condition repaired ${pct(values[0])} of its failed first runs (${fraction(pooled.hits, pooled.total)} overall), and with only ${sizeRange} failures per condition the intervals are wide: no detectable effect.`
    : overlap
    ? `Pooled repair rates ranged from ${pct(Math.min(...values))} to ${pct(Math.max(...values))}, each from only ${sizeRange} failed first runs, and every 95% interval overlaps the others: no detectable effect.`
    : "The repair rates differ by condition; read the intervals before drawing conclusions.";
  const ceiling =
    hostedRepair.total === 0
      ? "Hosted models never failed a first run, so there was nothing to repair"
      : `Hosted models fixed ${fraction(hostedRepair.hits, hostedRepair.total)} failed first runs whatever the feedback`;

  return `${headline} ${ceiling} (the ceiling), while ${localName} fixed ${fraction(localRepair.hits, localRepair.total)} (the floor).`;
}

export function RepairSection(props: SectionProps) {
  const { summary, runId } = props;
  const rows = repairRows(props);
  const conditions = conditionsForRun(summary, runId);
  const labelOf = (id: string) => conditions.find((c) => c.id === id)?.label ?? id;
  const models = modelsForRun(summary, runId);

  const chartRows: IntervalRow[] = rows
    .filter((row) => row.rate.value != null)
    .map((row) => ({
      key: row.condition,
      label: labelOf(row.condition),
      name: labelOf(row.condition),
      value: row.rate.value ?? 0,
      low: row.rate.low ?? 0,
      high: row.rate.high ?? 1,
      hits: row.rate.hits,
      total: row.rate.total,
    }));

  const columns: Column<RepairRow>[] = [
    { key: "condition", header: "Condition", render: (row) => labelOf(row.condition) },
    { key: "rate", header: "Repaired", numeric: true, render: (row) => pct(row.rate.value) },
    {
      key: "ci",
      header: "95% interval",
      numeric: true,
      render: (row) => `${pct(row.rate.low)}–${pct(row.rate.high)}`,
    },
    { key: "n", header: "Fixed / failed", numeric: true, render: (row) => fraction(row.rate.hits, row.rate.total) },
    ...models.map((model) => ({
      key: model,
      header: modelShort(model),
      numeric: true,
      render: (row: RepairRow) => {
        const rate = findCell(summary, runId, model, row.condition)?.repair;
        return rate && rate.total > 0 ? fraction(rate.hits, rate.total) : "–";
      },
    })),
  ];

  return (
    <BenchmarkSection
      id="repair"
      eyebrow="Error messages"
      title="Did better error messages help?"
      takeaway={takeawayFor(props, rows)}
    >
      <ChartCard
        title="Repair rate by feedback condition, all models pooled"
        subtitle="Of the episodes whose first run failed, the share that still ended in a pass."
        table={<DataTable caption="Repair rate by condition" columns={columns} rows={rows} rowKey={(r) => r.condition} />}
        howToRead={
          <>
            The dot is the observed repair rate; the line is its 95% Wilson interval, the range the true
            rate plausibly sits in. n is the number of failed first runs behind each dot. When intervals
            overlap this much, the data can't tell the conditions apart. The table splits each condition
            by model (fixed / failed; – means that model never failed a first run there).
          </>
        }
      >
        <IntervalChart rows={chartRows} axisLabel="Repair rate (dot) with 95% interval" />
      </ChartCard>
    </BenchmarkSection>
  );
}
