import { ModelChip } from "../../../components/ui/ModelChip";
import { fraction, pct } from "../../../lib/format";
import { modelColor, modelShort } from "../../../lib/models";
import type { ModelStats } from "../../../lib/types";
import { BarList, type BarRow } from "../chart/BarList";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { TipBody } from "../chart/Tooltip";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { minBy, splitHosted, statsForRun } from "../lib/derive";
import type { SectionProps } from "../lib/sections";

const failures = (row: ModelStats) => row.episodes - row.pass.hits;

function takeawayFor({ summary, runId }: SectionProps) {
  const { hosted, local } = splitHosted(summary, statsForRun(summary, runId));
  const laxest = minBy(hosted, (row) => row.tested.value ?? 1);
  if (!laxest) return "";
  const others = hosted.filter((row) => row !== laxest).map((row) => row.tested.value ?? 0);
  const othersRange = others.length
    ? `${pct(Math.min(...others))}${Math.min(...others) === Math.max(...others) ? "" : `–${pct(Math.max(...others))}`}`
    : "";
  const hostedFailures = hosted.reduce((sum, row) => sum + failures(row), 0);
  const onlyLaxestFailed = hostedFailures > 0 && failures(laxest) === hostedFailures;
  const localRow = local[0];

  return (
    <>
      {modelShort(laxest.model)} ran its code before submitting in only {pct(laxest.tested.value)} of tool
      episodes ({fraction(laxest.tested.hits, laxest.tested.total)}); the other hosted models tested in{" "}
      {othersRange}.{" "}
      {onlyLaxestFailed &&
        `All ${hostedFailures} hosted-model failures in this run were its untested submissions: the habit, not the skill, cost it a perfect score. `}
      {localRow &&
        `${modelShort(localRow.model)} ran its code in ${fraction(localRow.tested.hits, localRow.tested.total)} tool episodes.`}
    </>
  );
}

export function TestingSection({ summary, runId }: SectionProps) {
  const stats = statsForRun(summary, runId);

  const rows: BarRow[] = stats.map((row) => ({
    key: row.model,
    label: <ModelChip model={row.model} />,
    share: row.tested.value,
    color: modelColor(row.model),
    value: `${pct(row.tested.value)} · ${fraction(row.tested.hits, row.tested.total)}`,
    tip: (
      <TipBody
        keyColor={modelColor(row.model)}
        value={`${pct(row.tested.value)} tested first`}
        label={`${modelShort(row.model)} · ${fraction(row.tested.hits, row.tested.total)} tool episodes`}
        detail={`First run worked: ${pct(row.first_run_ok.value)} (${fraction(row.first_run_ok.hits, row.first_run_ok.total)})`}
      />
    ),
    ariaLabel: `${modelShort(row.model)}: tested first in ${pct(row.tested.value)} of tool episodes (${row.tested.hits} of ${row.tested.total})`,
  }));

  const columns: Column<ModelStats>[] = [
    { key: "model", header: "Model", render: (row) => modelShort(row.model) },
    { key: "tested", header: "Tested first", numeric: true, render: (row) => pct(row.tested.value) },
    { key: "testedN", header: "Tested / tool episodes", numeric: true, render: (row) => fraction(row.tested.hits, row.tested.total) },
    { key: "first", header: "First run worked", numeric: true, render: (row) => `${pct(row.first_run_ok.value)} (${fraction(row.first_run_ok.hits, row.first_run_ok.total)})` },
    { key: "runs", header: "Avg runs", numeric: true, render: (row) => (row.avg_runs == null ? "–" : row.avg_runs.toFixed(2)) },
    { key: "pass", header: "Pass rate", numeric: true, render: (row) => pct(row.pass.value) },
  ];

  return (
    <BenchmarkSection
      id="testing"
      eyebrow="Testing habits"
      title="Did models test before submitting?"
      takeaway={takeawayFor({ summary, runId })}
    >
      <ChartCard
        title="Tested before submitting"
        subtitle="Share of tool episodes (every condition except one-shot) where the model ran its code at least once before submitting."
        table={<DataTable caption="Testing habits by model" columns={columns} rows={stats} rowKey={(r) => r.model} />}
        howToRead={
          <>
            A full bar means the model always checked its program with the compiler before handing it in.
            Feedback quality can only matter when the model asks for feedback. Hover a bar, or open the
            table, for how often the first run already worked.
          </>
        }
      >
        <BarList rows={rows} track valueWidth="w-24" />
      </ChartCard>
    </BenchmarkSection>
  );
}
