import { Sparkles } from "lucide-react";
import { useMemo } from "react";
import { cn } from "../../lib/cn";
import type { Episode } from "../../lib/types";
import { applyFilters, type Filters } from "./filters";
import { activePreset, PRESETS } from "./presets";

interface PresetChipsProps {
  filters: Filters;
  episodes: Episode[];
  onSelect: (filters: Filters) => void;
}

/** Featured views. Each chip shows how many episodes it matches. */
export function PresetChips({ filters, episodes, onSelect }: PresetChipsProps) {
  const active = activePreset(filters);
  const counts = useMemo(
    () => PRESETS.map((preset) => applyFilters(episodes, preset.filters).length),
    [episodes],
  );
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-muted">
        <Sparkles className="size-3.5" aria-hidden />
        Featured
      </span>
      {PRESETS.map((preset, index) => {
        const selected = preset.id === active;
        const matches = counts[index];
        return (
          <button
            key={preset.id}
            type="button"
            aria-pressed={selected}
            title={preset.description}
            onClick={() => onSelect(preset.filters)}
            className={cn(
              "inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset transition",
              selected
                ? "bg-accent-soft/70 text-accent-ink ring-accent/40"
                : "bg-surface text-ink-2 ring-border-strong hover:bg-surface-2 hover:text-ink",
            )}
          >
            {preset.label}
            <span className={cn("rounded-full px-1.5 text-xs tabular-nums", selected ? "bg-surface/60" : "bg-surface-2")}>
              {matches}
            </span>
          </button>
        );
      })}
    </div>
  );
}
