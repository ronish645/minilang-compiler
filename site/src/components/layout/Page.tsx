import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

/** Standard page width and gutters (16px on phones). */
export function Container({ children, className }: { children?: ReactNode; className?: string }) {
  return <div className={cn("mx-auto w-full max-w-7xl px-4 sm:px-6", className)}>{children}</div>;
}

interface PageHeaderProps {
  eyebrow?: string;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
}

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <div className="border-b border-border bg-surface/40">
      <Container className="flex flex-col gap-4 py-10 sm:py-12 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-3xl">
          {eyebrow && (
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-accent">{eyebrow}</p>
          )}
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">{title}</h1>
          {description && <p className="mt-3 text-base text-ink-2 sm:text-lg">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
      </Container>
    </div>
  );
}
