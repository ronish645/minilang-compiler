import { ChevronDown } from "lucide-react";
import { useId } from "react";
import type { Task } from "../../lib/types";
import { ALL } from "./filters";

interface TaskSelectProps {
  tasks: Task[]; // already ordered by tier
  value: string;
  onChange: (value: string) => void;
}

/** The shared Select only takes flat options; this one groups tasks by tier with <optgroup>. Classes match Select exactly. */
export function TaskSelect({ tasks, value, onChange }: TaskSelectProps) {
  const id = useId();
  const tiers = [...new Set(tasks.map((task) => task.tier))];
  return (
    <label htmlFor={id} className="flex min-w-0 flex-col gap-1">
      <span className="text-xs font-medium text-ink-2">Task</span>
      <span className="relative">
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="h-9 w-full appearance-none rounded-lg bg-surface pl-3 pr-8 text-sm text-ink ring-1 ring-inset ring-border-strong focus:outline-none focus:ring-2 focus:ring-accent"
        >
          <option value={ALL}>All tasks</option>
          {tiers.map((tier) => (
            <optgroup key={tier} label={`Tier ${tier}`}>
              {tasks
                .filter((task) => task.tier === tier)
                .map((task) => (
                  <option key={task.id} value={task.id}>
                    {task.id}
                  </option>
                ))}
            </optgroup>
          ))}
        </select>
        <ChevronDown
          aria-hidden
          className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
        />
      </span>
    </label>
  );
}
