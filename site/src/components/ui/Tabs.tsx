import type { ReactNode } from "react";
import { cn } from "../../lib/cn";
import { rovingKeyDown } from "../../lib/rovingFocus";

export interface TabItem<T extends string> {
  id: T;
  label: string;
  icon?: ReactNode;
  badge?: ReactNode;
}

interface TabsProps<T extends string> {
  tabs: TabItem<T>[];
  active: T;
  onChange: (id: T) => void;
  label: string;
  className?: string;
}

/** An underlined tab bar. The caller renders the active panel. */
export function Tabs<T extends string>({ tabs, active, onChange, label, className }: TabsProps<T>) {
  return (
    <div
      role="tablist"
      aria-label={label}
      className={cn("flex gap-1 overflow-x-auto border-b border-border", className)}
      onKeyDown={(event) => rovingKeyDown(event, tabs.map((t) => t.id), active, onChange)}
    >
      {tabs.map((tab) => {
        const selected = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            data-roving
            aria-selected={selected}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(tab.id)}
            className={cn(
              "-mb-px inline-flex items-center gap-1.5 whitespace-nowrap border-b-2 px-3 py-2 text-sm font-medium transition",
              selected
                ? "border-accent text-ink"
                : "border-transparent text-ink-2 hover:text-ink",
            )}
          >
            {tab.icon}
            {tab.label}
            {tab.badge}
          </button>
        );
      })}
    </div>
  );
}
