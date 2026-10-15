import { ChevronDown } from "lucide-react";
import { useId } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  label: string;
  value: string;
  options: SelectOption[];
  onChange: (value: string) => void;
}

/** A labelled native select (keyboard and screen-reader friendly for free). */
export function Select({ label, value, options, onChange }: SelectProps) {
  const id = useId();
  return (
    <label htmlFor={id} className="flex min-w-0 flex-col gap-1">
      <span className="text-xs font-medium text-ink-2">{label}</span>
      <span className="relative">
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="h-9 w-full appearance-none rounded-lg bg-surface pl-3 pr-8 text-sm text-ink ring-1 ring-inset ring-border-strong focus:outline-none focus:ring-2 focus:ring-accent"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
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
