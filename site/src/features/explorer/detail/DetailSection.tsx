import type { ReactNode } from "react";

/** A titled block inside the episode drawer. */
export function DetailSection({ title, children, aside }: { title: string; children: ReactNode; aside?: ReactNode }) {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">{title}</h3>
        {aside}
      </div>
      {children}
    </section>
  );
}
