// The four headline findings, each built from summary.json. The prose around
// the numbers is fixed; the numbers are not.
import { pct } from "../../lib/format";
import { modelShort } from "../../lib/models";
import type { Summary } from "../../lib/types";
import {
  costPerSolve,
  hostedFailures,
  hostedFirstRunOk,
  hostedPass,
  localRepairs,
  runIds,
  runShortTitle,
} from "./overviewStats";

export type FindingSection = "heatmap" | "repair" | "testing" | "cost";

export interface Finding {
  section: FindingSection;
  run: string; // the run the figure comes from; the link opens the Benchmark page on it
  figure: string;
  figureLabel: string;
  title: string;
  body: string;
  linkLabel: string;
}

const tierOf = (summary: Summary, model: string) =>
  summary.models.find((info) => info.id === model)?.tier;

function specFinding(summary: Summary, runs: string[]): Finding {
  const [main, ...later] = runs.map((run) => ({ run, tally: hostedPass(summary, run) }));
  const laterText = later
    .map(({ run, tally }) => `${runShortTitle(summary, run)}: ${tally.hits}/${tally.total}`)
    .join("; ");
  return {
    section: "heatmap",
    run: main.run,
    figure: `${main.tally.hits}/${main.tally.total}`,
    figureLabel: `hosted-model episodes passed (${runShortTitle(summary, main.run)})`,
    title: "Frontier models learned it from the spec alone",
    body: `Including tasks built to punish JavaScript and Python habits, and with no tools at all in one-shot. ${laterText}.`,
    linkLabel: "Pass rate by model and condition",
  };
}

function feedbackFinding(summary: Summary, runs: string[]): Finding {
  const ceiling = hostedFirstRunOk(summary, runs[0]);
  const floors = runs
    .map((run) => ({ run, repair: localRepairs(summary, run) }))
    .filter((item) => item.repair && item.repair.total > 0)
    .map(({ run, repair }) => `${repair?.hits} of ${repair?.total} (${runShortTitle(summary, run)})`);
  const local = localRepairs(summary, runs[0]);
  return {
    section: "repair",
    run: runs[0],
    figure: pct(ceiling.rate),
    figureLabel: `of hosted models' first runs already worked (${runShortTitle(summary, runs[0])})`,
    title: "Error-message quality made no detectable difference",
    body: `A ceiling and a floor: hosted models rarely needed feedback, and ${modelShort(local?.model ?? "")} fixed only ${floors.join(" and ")} failed first runs. The intervals overlap, so this is "no detectable effect", not "no effect".`,
    linkLabel: "Repair rate by condition",
  };
}

function testingFinding(summary: Summary, run: string): Finding {
  const failures = hostedFailures(summary, run);
  return {
    section: "testing",
    run,
    figure: `${failures.count}/${failures.total}`,
    figureLabel: `hosted failures came from ${modelShort(failures.model)} (${runShortTitle(summary, run)})`,
    title: "Untested submissions caused every hosted failure",
    body: `Each one was code ${modelShort(failures.model)} submitted without running it first. It tested before submitting in only ${pct(failures.tested?.value)} of its tool episodes; the other hosted models almost always did.`,
    linkLabel: "Who tests before submitting",
  };
}

function costFinding(summary: Summary, run: string): Finding {
  const rows = costPerSolve(summary, run);
  const small = rows.filter((row) => tierOf(summary, row.model) === "small");
  const mid = rows.filter((row) => tierOf(summary, row.model) === "mid");
  const cheapest = small[0];
  const bestMid = mid[0];
  const factor = cheapest && bestMid ? bestMid.perSolve / cheapest.perSolve : null;
  const allCheaper = small.length > 0 && mid.length > 0 && small[small.length - 1].perSolve < mid[0].perSolve;
  return {
    section: "cost",
    run,
    figure: factor ? `${Math.round(factor)}×` : "–",
    figureLabel: `lower cost per solve: ${modelShort(cheapest?.model ?? "")} vs ${modelShort(bestMid?.model ?? "")}`,
    title: "The cheapest models were the best value",
    body: `${modelShort(cheapest?.model ?? "")} passed ${pct(cheapest?.passRate)} of its episodes${
      allCheaper ? ", and both small models cost less per solve than either mid-tier model" : ""
    } (${runShortTitle(summary, run)}).`,
    linkLabel: "Cost per solve",
  };
}

export function buildFindings(summary: Summary): Finding[] {
  const runs = runIds(summary);
  if (runs.length === 0) return [];
  return [
    specFinding(summary, runs),
    feedbackFinding(summary, runs),
    testingFinding(summary, runs[0]),
    costFinding(summary, runs[0]),
  ];
}

export const findingHref = (finding: Finding) =>
  `/benchmark?run=${encodeURIComponent(finding.run)}&section=${finding.section}`;
