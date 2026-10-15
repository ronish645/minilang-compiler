import { RotateCcw, Search } from "lucide-react";
import { useId } from "react";
import { Button } from "../../components/ui/Button";
import { SegmentedControl } from "../../components/ui/SegmentedControl";
import { Select } from "../../components/ui/Select";
import { count } from "../../lib/format";
import { OUTCOME_LABEL } from "../../lib/models";
import type { Outcome } from "../../lib/types";
import { ALL, FAILED, isDefault, type Filters } from "./filters";
import type { Lookups } from "./lookups";
import { TaskSelect } from "./TaskSelect";

interface FilterBarProps {
  filters: Filters;
  onChange: (patch: Partial<Filters>) => void;
  onReset: () => void;
  lookups: Lookups;
  outcomes: Outcome[]; // outcomes present in the data
  shown: number;
  total: number;
}

function SearchBox({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex min-w-0 flex-col gap-1">
      <span className="text-xs font-medium text-ink-2">Search</span>
      <span className="relative">
        <Search aria-hidden className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted" />
        <input
          id={id}
          type="search"
          value={value}
          placeholder="Task, code or error…"
          onChange={(event) => onChange(event.target.value)}
          className="h-9 w-full rounded-lg bg-surface pl-8 pr-3 text-sm text-ink ring-1 ring-inset ring-border-strong placeholder:text-muted focus:outline-none focus:ring-2 focus:ring-accent"
        />
      </span>
    </label>
  );
}

export function FilterBar({ filters, onChange, onReset, lookups, outcomes, shown, total }: FilterBarProps) {
  const runOptions = [{ value: ALL, label: "All runs" }, ...lookups.runs.map((run) => ({ value: run.id, label: run.label }))];
  const outcomeOptions = [
    { value: ALL, label: "All outcomes" },
    { value: "passed", label: "Passed" },
    { value: FAILED, label: "Any failure" },
    ...outcomes.filter((o) => o !== "passed").map((o) => ({ value: o, label: OUTCOME_LABEL[o] ?? o })),
  ];

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <SegmentedControl label="Run" options={runOptions} value={filters.run} onChange={(run) => onChange({ run })} />
        <div className="flex items-center gap-3">
          <p className="text-sm text-ink-2" aria-live="polite">
            <span className="font-semibold text-ink tabular-nums">{count(shown)}</span> of {count(total)} episodes
          </p>
          <Button size="sm" variant="ghost" onClick={onReset} disabled={isDefault(filters)} icon={<RotateCcw className="size-3.5" aria-hidden />}>
            Reset
          </Button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-[repeat(4,minmax(0,1fr))_minmax(0,1.4fr)]">
        <Select
          label="Model"
          value={filters.model}
          onChange={(model) => onChange({ model })}
          options={[{ value: ALL, label: "All models" }, ...lookups.models.map((m) => ({ value: m.id, label: m.label }))]}
        />
        <Select
          label="Condition"
          value={filters.condition}
          onChange={(condition) => onChange({ condition })}
          options={[{ value: ALL, label: "All conditions" }, ...lookups.conditions.map((c) => ({ value: c.id, label: c.label }))]}
        />
        <Select label="Outcome" value={filters.outcome} onChange={(outcome) => onChange({ outcome })} options={outcomeOptions} />
        <TaskSelect tasks={lookups.tasks} value={filters.task} onChange={(task) => onChange({ task })} />
        <div className="col-span-2 md:col-span-2 xl:col-span-1">
          <SearchBox value={filters.q} onChange={(q) => onChange({ q })} />
        </div>
      </div>
    </div>
  );
}
