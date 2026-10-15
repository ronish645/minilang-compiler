import { useState } from "react";
import { Select } from "../../../components/ui/Select";
import { modelColor, modelShort } from "../../../lib/models";
import type { ErrorPattern } from "../../../lib/types";
import { BarList, type BarRow } from "../chart/BarList";
import { ChartCard } from "../chart/ChartCard";
import { DataTable, type Column } from "../chart/DataTable";
import { TipBody } from "../chart/Tooltip";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { isLocalModel, modelsForRun } from "../lib/derive";
import { ERROR_HABITS } from "../lib/errorHabits";
import type { SectionProps } from "../lib/sections";
import { HabitList } from "./HabitList";

const DEFAULT_MODEL = "qwen-3b-local";
const EXPLAINED = 3;

export function ErrorsSection({ summary, runId }: SectionProps) {
  const [chosen, setChosen] = useState(DEFAULT_MODEL);
  const runPatterns = summary.error_patterns.filter((row) => row.run === runId);
  const available = modelsForRun(summary, runId).filter((model) => runPatterns.some((row) => row.model === model));
  const model = available.includes(chosen) ? chosen : (available[0] ?? chosen);
  const patterns = runPatterns.filter((row) => row.model === model).sort((a, b) => b.count - a.count);
  const max = Math.max(...patterns.map((row) => row.count), 1);
  const top = patterns[0];

  const rows: BarRow[] = patterns.map((row) => ({
    key: row.pattern,
    label: <code className="break-words font-mono text-[13px] text-ink">{row.pattern}</code>,
    share: row.count / max,
    color: modelColor(model),
    value: `${row.count}×`,
    tip: (
      <TipBody
        keyColor={modelColor(model)}
        value={`${row.count} times`}
        label={row.pattern}
        detail={ERROR_HABITS[row.pattern]?.habit}
      />
    ),
    ariaLabel: `${row.pattern}: ${row.count} times`,
  }));

  const columns: Column<ErrorPattern>[] = [
    { key: "pattern", header: "Error pattern", render: (row) => <code className="font-mono text-[13px]">{row.pattern}</code> },
    { key: "count", header: "Count", numeric: true, render: (row) => row.count },
    { key: "habit", header: "Likely habit", render: (row) => ERROR_HABITS[row.pattern]?.habit ?? "–" },
  ];

  const takeaway = top
    ? `${modelShort(model)}'s most frequent compiler error was "${top.pattern}" (${top.count} times).${
        isLocalModel(summary, model)
          ? " Most of its errors are syntax carried over from Python and JavaScript, not a misunderstanding of the task."
          : ""
      }`
    : "No compiler errors were recorded for this model in this run.";

  return (
    <BenchmarkSection id="errors" eyebrow="Common errors" title="What goes wrong for the small model?" takeaway={takeaway}>
      <ChartCard
        title="Most common compiler errors"
        subtitle="Error messages with names and values masked as …, counted across the model's runs."
        controls={
          available.length > 0 && (
            <div className="w-full max-w-56">
              <Select
                label="Model"
                value={model}
                onChange={setChosen}
                options={available.map((id) => ({ value: id, label: modelShort(id) }))}
              />
            </div>
          )
        }
        table={<DataTable caption={`Compiler errors for ${modelShort(model)}`} columns={columns} rows={patterns} rowKey={(r) => r.pattern} />}
        howToRead={
          <>
            Each bar is one kind of error, longest first. The patterns hide variable names so that the
            same mistake is counted once, whatever the program called its variables. Below the chart, the
            top few are matched to the habit that usually causes them.
          </>
        }
      >
        <BarList rows={rows} layout="above" valueWidth="w-10" />
        <HabitList patterns={patterns.slice(0, EXPLAINED)} />
      </ChartCard>
    </BenchmarkSection>
  );
}
