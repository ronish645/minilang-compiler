import { CalendarDays, Cloud, Coins, Laptop, ListChecks } from "lucide-react";
import { Card } from "../../../components/ui/Card";
import { SegmentedControl } from "../../../components/ui/SegmentedControl";
import { StatTile } from "../../../components/ui/StatTile";
import { count, fraction, pct, usd } from "../../../lib/format";
import { modelShort } from "../../../lib/models";
import type { Summary } from "../../../lib/types";
import {
  conditionsForRun,
  findRun,
  poolRates,
  runCost,
  runsNewestFirst,
  splitHosted,
  statsForRun,
  tasksInRun,
} from "../lib/derive";
import { runShortLabel } from "../../../lib/runs";

interface RunOverviewProps {
  summary: Summary;
  runId: string;
  onRunChange: (runId: string) => void;
}

const formatDate = (iso: string) =>
  new Date(`${iso}T12:00:00`).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });

/** The run picker (it scopes everything below) plus the run's headline numbers. */
export function RunOverview({ summary, runId, onRunChange }: RunOverviewProps) {
  const run = findRun(summary, runId);
  if (!run) return null;

  const stats = statsForRun(summary, runId);
  const { hosted, local } = splitHosted(summary, stats);
  const hostedPass = poolRates(hosted.map((row) => row.pass));
  const localPass = poolRates(local.map((row) => row.pass));
  const localName = local.map((row) => modelShort(row.model)).join(", ") || "Local model";
  const options = runsNewestFirst(summary).map((r) => ({ value: r.id, label: runShortLabel(r) }));
  const grid = `${stats.length} models × ${tasksInRun(summary, runId)} tasks × ${conditionsForRun(summary, runId).length} conditions`;

  return (
    <div className="flex flex-col gap-4">
      <Card className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="min-w-0">
          <h2 className="text-base font-semibold text-ink">{run.title}</h2>
          <p className="mt-1 text-sm text-ink-2">{run.description}</p>
          <p className="mt-2 inline-flex items-center gap-1.5 text-xs text-muted">
            <CalendarDays aria-hidden className="size-3.5" />
            Run <code className="font-mono">{run.id}</code> · {formatDate(run.date)} · {count(run.episodes)}{" "}
            episodes
          </p>
        </div>
        <div className="flex shrink-0 flex-col gap-1">
          <span className="text-xs font-medium text-ink-2">Benchmark run</span>
          <SegmentedControl label="Benchmark run" options={options} value={runId} onChange={onRunChange} />
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <StatTile label="Episodes" icon={<ListChecks className="size-4" />} value={count(run.episodes)} detail={grid} />
        <StatTile
          label="Hosted models passed"
          icon={<Cloud className="size-4" />}
          value={pct(hostedPass.value, hostedPass.value === 1 ? 0 : 1)}
          detail={`${fraction(hostedPass.hits, hostedPass.total)} episodes, ${hosted.length} models`}
        />
        <StatTile
          label={`${localName} passed`}
          icon={<Laptop className="size-4" />}
          value={pct(localPass.value)}
          detail={`${fraction(localPass.hits, localPass.total)} episodes, running locally`}
        />
        <StatTile
          label="API cost"
          icon={<Coins className="size-4" />}
          value={usd(runCost(stats))}
          detail="The whole run; the local model is free"
        />
      </div>
    </div>
  );
}
