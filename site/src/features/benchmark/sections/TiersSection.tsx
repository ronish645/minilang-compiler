import { ArrowRight, Layers } from "lucide-react";
import { Button } from "../../../components/ui/Button";
import { Card } from "../../../components/ui/Card";
import { fraction, pct } from "../../../lib/format";
import { modelShort } from "../../../lib/models";
import type { TierRow } from "../../../lib/types";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { isLocalModel, minBy, modelsForRun } from "../lib/derive";
import { runShortLabel } from "../../../lib/runs";
import type { SectionProps } from "../lib/sections";
import { TierPanels } from "./TierPanels";

interface TiersSectionProps extends SectionProps {
  onRunChange: (runId: string) => void;
}

const tierRows = ({ summary, runId }: SectionProps) => summary.tiers.filter((row) => row.run === runId);

/** The run with the most tiers, used to offer a switch from a single-tier run. */
const multiTierRun = ({ summary }: SectionProps) =>
  summary.runs.find((run) => new Set(summary.tiers.filter((t) => t.run === run.id).map((t) => t.tier)).size > 1);

function takeawayFor(props: SectionProps, rows: TierRow[]) {
  const hosted = rows.filter((row) => !isLocalModel(props.summary, row.model));
  const local = rows.filter((row) => isLocalModel(props.summary, row.model)).sort((a, b) => a.tier - b.tier);
  const weakest = minBy(hosted, (row) => row.pass.value ?? 1);
  const first = local[0];
  const last = local[local.length - 1];
  if (!weakest || !first || !last) return "";
  return (
    <>
      Hosted models stayed at {pct(weakest.pass.value)} or higher on every tier (lowest: {modelShort(weakest.model)}{" "}
      on tier {weakest.tier}, {fraction(weakest.pass.hits, weakest.pass.total)}). {modelShort(first.model)} fell from{" "}
      {pct(first.pass.value)} on tier {first.tier} to {pct(last.pass.value)} on tier {last.tier}, where the spec traps
      combine.
    </>
  );
}

function SingleTierNote({ props, rows, onRunChange }: { props: SectionProps; rows: TierRow[]; onRunChange: (id: string) => void }) {
  const target = multiTierRun(props);
  const tier = rows[0]?.tier;
  return (
    <Card className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex gap-3">
        <Layers aria-hidden className="mt-0.5 size-5 shrink-0 text-muted" />
        <p className="text-sm text-ink-2">
          This run uses a single tier{tier != null && ` (tier ${tier})`}, so there is no tier-by-tier breakdown. Per-model
          results for it are in the pass-rate and outcome charts above.
        </p>
      </div>
      {target && (
        <Button size="sm" className="shrink-0 whitespace-nowrap" onClick={() => onRunChange(target.id)} icon={<ArrowRight className="size-4" />}>
          Show {runShortLabel(target)}
        </Button>
      )}
    </Card>
  );
}

export function TiersSection({ onRunChange, ...props }: TiersSectionProps) {
  const rows = tierRows(props);
  const tiers = [...new Set(rows.map((row) => row.tier))].sort((a, b) => a - b);
  const models = modelsForRun(props.summary, props.runId);
  const single = tiers.length < 2;

  const columns: Column<string>[] = [
    { key: "model", header: "Model", render: (model) => modelShort(model) },
    ...tiers.map((tier) => ({
      key: `t${tier}`,
      header: `Tier ${tier}`,
      numeric: true,
      render: (model: string) => {
        const rate = rows.find((row) => row.model === model && row.tier === tier)?.pass;
        return rate ? `${pct(rate.value)} (${fraction(rate.hits, rate.total)})` : "–";
      },
    })),
  ];

  return (
    <BenchmarkSection
      id="tiers"
      eyebrow="Task tiers"
      title="Where does it get hard?"
      takeaway={single ? "Tier breakdowns need a run with more than one tier." : takeawayFor(props, rows)}
    >
      {single ? (
        <SingleTierNote props={props} rows={rows} onRunChange={onRunChange} />
      ) : (
        <ChartCard
          title="Pass rate by task tier"
          subtitle="All conditions pooled within each tier. Tier 3–4 tasks are built to punish JavaScript and Python habits."
          table={<DataTable caption="Pass rate by tier and model" columns={columns} rows={models} rowKey={(m) => m} />}
          howToRead={
            <>
              One small panel per model, all on the same 0–100% scale, so panels compare directly. Columns
              run from tier 1 (basics) to tier 4 (combined traps). The methodology section below describes
              each tier.
            </>
          }
        >
          <TierPanels models={models} rows={rows} />
        </ChartCard>
      )}
    </BenchmarkSection>
  );
}
