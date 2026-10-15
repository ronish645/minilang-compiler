import { BookOpen, ChevronDown } from "lucide-react";
import { useId } from "react";
import { EXAMPLE_GROUPS, EXAMPLES } from "./examples";

export const CUSTOM_ID = "custom";

interface ExamplePickerProps {
  value: string;
  onChange: (id: string) => void;
}

/** A native <select> with optgroups: keyboard and screen-reader friendly for free. */
export function ExamplePicker({ value, onChange }: ExamplePickerProps) {
  const id = useId();
  return (
    <div className="relative min-w-[11rem] flex-1 sm:max-w-[260px]">
      <label htmlFor={id} className="sr-only">
        Example program
      </label>
      <BookOpen
        aria-hidden
        className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
      />
      <select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-8 w-full appearance-none truncate rounded-lg bg-surface pl-8 pr-8 text-sm text-ink ring-1 ring-inset ring-border-strong hover:bg-surface-2 focus:outline-none focus:ring-2 focus:ring-accent"
      >
        {value === CUSTOM_ID && <option value={CUSTOM_ID}>Your program</option>}
        {EXAMPLE_GROUPS.map((group) => (
          <optgroup key={group} label={group}>
            {EXAMPLES.filter((e) => e.group === group).map((example) => (
              <option key={example.id} value={example.id}>
                {example.title}
              </option>
            ))}
          </optgroup>
        ))}
      </select>
      <ChevronDown
        aria-hidden
        className="pointer-events-none absolute right-2.5 top-1/2 size-4 -translate-y-1/2 text-muted"
      />
    </div>
  );
}
