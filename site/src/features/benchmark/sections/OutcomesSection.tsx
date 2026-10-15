import { count, pct } from "../../../lib/format";
import { modelShort } from "../../../lib/models";
import type { ModelStats } from "../../../lib/types";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { Legend } from "../chart/Legend";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { maxBy, splitHosted, statsForRun } from "../lib/derive";
import { OUTCOME_STYLES, outcomeCount } from "../lib/outcomes";
import type { SectionProps } from "../lib/sections";
import { OutcomesChart } from "./OutcomesChart";

const failures = (row: ModelStats) => row.episodes - row.pass.hits;

function takeawayFor({ summary, runId }: SectionProps) {
  const { hosted, local } = splitHosted(summary, statsForRun(summary, runId));
  const hostedFailures = hosted.reduce((sum, row) => sum + failures(row), 0);
  const failingHosted = hosted.filter((row) => failures(row) > 0);
  const localRow = local[0];
  const topFailure = localRow
    ? maxBy(
        OUTCOME_STYLES.filter((style) => style.key !== "passed"),
        (style) => outcomeCount(localRow.outcomes, style),
      )
    : undefined;

  const hostedText =
    hostedFailures === 0
      ? "No hosted model failed a single episode in this run."
      : `Hosted models failed ${hostedFailures} episode${hostedFailures === 1 ? "" : "s"}, all from ${failingHosted
          .map((row) => modelShort(row.model))
          .join(" and ")}.`;

  if (!localRow || !topFailure) return hostedText;
  const n = outcomeCount(localRow.outcomes, topFailure);
  return (
    <>
      {hostedText} {modelShort(localRow.model)}'s most common failure was a{" "}
      {topFailure.label.toLowerCase()} ({n} of {localRow.episodes} episodes), and it wrote no code at all
      in {localRow.outcomes.no_code ?? 0}.
    </>
  );
}

export function OutcomesSection({ summary, runId }: SectionProps) {
  const stats = statsForRun(summary, runId);
  const present = OUTCOME_STYLES.filter((style) => stats.some((row) => outcomeCount(row.outcomes, style) > 0));

  const columns: Column<ModelStats>[] = [
    { key: "model", header: "Model", render: (row) => modelShort(row.model) },
    ...present.map((style) => ({
      key: style.key,
      header: style.label,
      numeric: true,
      render: (row: ModelStats) => {
        const n = outcomeCount(row.outcomes, style);
        return `${count(n)} (${pct(n / row.episodes)})`;
      },
    })),
    { key: "episodes", header: "Episodes", numeric: true, render: (row) => count(row.episodes) },
  ];

  return (
    <BenchmarkSection
      id="outcomes"
      eyebrow="Outcomes"
      title="How do models fail?"
      takeaway={takeawayFor({ summary, runId })}
    >
      <ChartCard
        title="Episode outcomes by model"
        subtitle="Every episode ends in exactly one outcome. Bars show each model's split, out of 100%."
        legend={
          <Legend
            label="Outcomes"
            items={present.map((style) => ({ key: style.key, label: style.label, color: style.color, icon: style.icon }))}
          />
        }
        table={<DataTable caption="Episode outcomes by model" columns={columns} rows={stats} rowKey={(r) => r.model} />}
        howToRead={
          <>
            Colors here mean a <em>state</em>, not a model: green passed, then yellow, orange and red as the
            program got less far (wrong output, crashed while running, never compiled). Gray means the
            model never produced a program. Each segment's icon and name are in the legend.
          </>
        }
      >
        <OutcomesChart stats={stats} />
      </ChartCard>
    </BenchmarkSection>
  );
}
