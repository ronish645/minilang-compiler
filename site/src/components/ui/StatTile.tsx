import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

interface StatTileProps {
  label: string;
  value: ReactNode;
  detail?: ReactNode;
  icon?: ReactNode;
  className?: string;
}

/** A headline number. Sometimes the right "chart" is just one figure. */
export function StatTile({ label, value, detail, icon, className }: StatTileProps) {
  return (
    <div className={cn("rounded-2xl border border-border bg-surface p-5", className)}>
      <div className="flex items-center gap-2 text-sm font-medium text-ink-2">
        {icon && <span className="text-muted">{icon}</span>}
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold tracking-tight text-ink">{value}</div>
      {detail && <div className="mt-1 text-sm text-ink-2">{detail}</div>}
    </div>
  );
}
