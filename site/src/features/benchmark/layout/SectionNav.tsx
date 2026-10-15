import { cn } from "../../../lib/cn";
import { SECTIONS } from "../lib/sections";

interface SectionNavProps {
  active: string | null;
  onSelect: (id: string) => void;
  runLabel: string;
}

const linkClass = (selected: boolean) =>
  cn(
    "rounded-md text-sm transition",
    selected ? "bg-surface-2 font-medium text-ink" : "text-ink-2 hover:text-ink",
  );

/** Desktop: a sticky sidebar. Phones and tablets: a sticky row of chips. */
export function SectionNav({ active, onSelect, runLabel }: SectionNavProps) {
  const items = SECTIONS.map((section) => ({ ...section, selected: section.id === active }));

  return (
    <>
      <nav
        aria-label="Benchmark sections"
        className="sticky top-16 z-30 -mx-4 border-b border-border bg-page/90 px-4 py-2 backdrop-blur-md sm:-mx-6 sm:px-6 lg:hidden"
      >
        <ul className="flex gap-1 overflow-x-auto">
          {items.map((item) => (
            <li key={item.id} className="shrink-0">
              <button
                type="button"
                aria-current={item.selected ? "true" : undefined}
                onClick={() => onSelect(item.id)}
                className={cn(linkClass(item.selected), "whitespace-nowrap px-2.5 py-1")}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
      </nav>

      <nav aria-label="Benchmark sections" className="sticky top-24 hidden self-start lg:block">
        <p className="px-2.5 text-xs font-semibold uppercase tracking-[0.14em] text-muted">On this page</p>
        <ul className="mt-3 flex flex-col gap-0.5 border-l border-border pl-2">
          {items.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                aria-current={item.selected ? "true" : undefined}
                onClick={() => onSelect(item.id)}
                className={cn(linkClass(item.selected), "w-full px-2.5 py-1.5 text-left")}
              >
                {item.label}
              </button>
            </li>
          ))}
        </ul>
        <p className="mt-6 px-2.5 text-xs text-muted">
          Showing <span className="font-medium text-ink-2">{runLabel}</span>
        </p>
      </nav>
    </>
  );
}
