import { fraction, pct } from "../../../lib/format";
import { modelShort } from "../../../lib/models";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { ScaleLegend } from "../chart/ScaleLegend";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import {
  conditionsForRun,
  findCell,
  isLocalModel,
  maxBy,
  minBy,
  modelsForRun,
  poolRates,
  splitHosted,
  statsForRun,
} from "../lib/derive";
import type { SectionProps } from "../lib/sections";
import { HeatmapChart } from "./HeatmapChart";
import { countWord } from "../lib/words";

function takeawayFor({ summary, runId }: SectionProps) {
  const { hosted, local } = splitHosted(summary, statsForRun(summary, runId));
  const hostedPass = poolRates(hosted.map((row) => row.pass));
  const cells = summary.cells.filter((cell) => cell.run === runId && cell.pass.value != null);
  const hostedCells = cells.filter((cell) => !isLocalModel(summary, cell.model));
  const localCells = cells.filter((cell) => isLocalModel(summary, cell.model));
  const hostedFloor = minBy(hostedCells, (cell) => cell.pass.value ?? 0)?.pass.value;
  const localLow = minBy(localCells, (cell) => cell.pass.value ?? 0)?.pass.value;
  const localHigh = maxBy(localCells, (cell) => cell.pass.value ?? 0)?.pass.value;
  const localPass = poolRates(local.map((row) => row.pass));
  const localName = local.map((row) => modelShort(row.model)).join(", ");

  return (
    <>
      The {countWord(hosted.length)} hosted models passed {fraction(hostedPass.hits, hostedPass.total)} episodes, and no
      model-condition cell fell below {pct(hostedFloor)}. {localName} passed{" "}
      {fraction(localPass.hits, localPass.total)}, between {pct(localLow)} and {pct(localHigh)} per
      condition. That is a ceiling and a floor, with nothing in between.
    </>
  );
}

export function HeatmapSection({ summary, runId }: SectionProps) {
  const models = modelsForRun(summary, runId);
  const conditions = conditionsForRun(summary, runId);
  const cellFor = (model: string, condition: string) => findCell(summary, runId, model, condition);
  const takeaway = takeawayFor({ summary, runId });

  const columns: Column<string>[] = [
    { key: "model", header: "Model", render: (model) => modelShort(model) },
    ...conditions.map((condition) => ({
      key: condition.id,
      header: condition.label,
      numeric: true,
      render: (model: string) => {
        const rate = cellFor(model, condition.id)?.pass;
        return rate ? `${pct(rate.value)} (${fraction(rate.hits, rate.total)})` : "–";
      },
    })),
  ];

  return (
    <BenchmarkSection id="heatmap" eyebrow="Pass rate" title="Who learned MiniLang from the spec?" takeaway={takeaway}>
      <ChartCard
        title="Pass rate by model and feedback condition"
        subtitle="Share of tasks where the submitted program printed exactly the expected output."
        legend={<ScaleLegend label="Pass rate" />}
        table={<DataTable caption="Pass rate by model and condition" columns={columns} rows={models} rowKey={(m) => m} />}
        howToRead={
          <>
            Each row is a model, each column a feedback condition (hover or focus a column name for what
            the model saw). Shading follows the scale above, and every cell prints its rate. One-shot is the hardest setting: the model
            writes the program once and never runs it.
          </>
        }
      >
        <HeatmapChart models={models} conditions={conditions} cellFor={cellFor} />
      </ChartCard>
    </BenchmarkSection>
  );
}
