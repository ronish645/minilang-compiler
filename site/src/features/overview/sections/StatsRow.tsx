import { Bot, CircleCheck, Coins, ListChecks, PlayCircle } from "lucide-react";
import { StatTile } from "../../../components/ui/StatTile";
import { count, usd } from "../../../lib/format";
import type { Summary } from "../../../lib/types";
import { hostedPass, runIds, runShortTitle } from "../overviewStats";

/** Headline numbers, all computed from summary.json. */
export function StatsRow({ summary }: { summary: Summary }) {
  const { totals } = summary;
  const local = summary.models.filter((model) => model.provider === "ollama").length;
  const tiers = new Set(summary.tiers.map((row) => row.tier)).size;
  const [mainRun, ...laterRuns] = runIds(summary);
  const main = hostedPass(summary, mainRun);
  const later = laterRuns.map((run) => ({ run, tally: hostedPass(summary, run) }));

  const iconClass = "size-4";
  return (
    <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-5">
      <StatTile
        label="Graded episodes"
        icon={<PlayCircle className={iconClass} aria-hidden />}
        value={count(totals.episodes)}
        detail={`across ${summary.runs.length} benchmark runs`}
      />
      <StatTile
        label="Models"
        icon={<Bot className={iconClass} aria-hidden />}
        value={totals.models}
        detail={`${totals.models - local} hosted · ${local} local`}
      />
      <StatTile
        label="Tasks"
        icon={<ListChecks className={iconClass} aria-hidden />}
        value={totals.tasks}
        detail={`${tiers} difficulty tiers`}
      />
      <StatTile
        label="Total API cost"
        icon={<Coins className={iconClass} aria-hidden />}
        value={usd(totals.cost_usd)}
        detail="for every episode"
      />
      <StatTile
        className="col-span-2 lg:col-span-1"
        label="Hosted models passed"
        icon={<CircleCheck className={iconClass} aria-hidden />}
        value={
          <>
            {main.hits}
            <span className="text-xl text-muted">/{main.total}</span>
          </>
        }
        detail={[
          runShortTitle(summary, mainRun),
          ...later.map(({ run, tally }) => `${runShortTitle(summary, run)}: ${tally.hits}/${tally.total}`),
        ].join(" · ")}
      />
    </div>
  );
}
