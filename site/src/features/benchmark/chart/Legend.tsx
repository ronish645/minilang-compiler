import type { LucideIcon } from "lucide-react";

export interface LegendItem {
  key: string;
  label: string;
  color: string;
  icon?: LucideIcon;
}

/** A legend row. Swatches are rects (they key bars and cells); text stays in ink. */
export function Legend({ items, label }: { items: LegendItem[]; label: string }) {
  return (
    <ul aria-label={label} className="flex flex-wrap gap-x-4 gap-y-2 text-xs text-ink-2">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <li key={item.key} className="inline-flex items-center gap-1.5">
            <span aria-hidden className="size-3 shrink-0 rounded-[3px]" style={{ background: item.color }} />
            {Icon && <Icon aria-hidden className="size-3.5 text-ink-2" />}
            {item.label}
          </li>
        );
      })}
    </ul>
  );
}
