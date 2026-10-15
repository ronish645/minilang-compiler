import { Info } from "lucide-react";
import { useState, type ReactNode } from "react";
import { Card, CardHeader } from "../../../components/ui/Card";
import { SegmentedControl } from "../../../components/ui/SegmentedControl";

type View = "chart" | "table";

const VIEW_OPTIONS = [
  { value: "chart" as const, label: "Chart" },
  { value: "table" as const, label: "Table" },
];

interface ChartCardProps {
  title: string;
  subtitle?: ReactNode;
  controls?: ReactNode;
  legend?: ReactNode;
  table: ReactNode;
  howToRead: ReactNode;
  children: ReactNode;
}

/** A chart's frame: title, Chart/Table toggle, optional legend, and a reading guide. */
export function ChartCard({ title, subtitle, controls, legend, table, howToRead, children }: ChartCardProps) {
  const [view, setView] = useState<View>("chart");

  return (
    <Card>
      <CardHeader
        title={title}
        subtitle={subtitle}
        action={
          <SegmentedControl
            label={`${title}: view as`}
            size="sm"
            options={VIEW_OPTIONS}
            value={view}
            onChange={setView}
          />
        }
      />
      {controls && <div className="mb-4 flex flex-wrap items-end gap-3">{controls}</div>}
      {view === "chart" ? (
        <>
          {legend && <div className="mb-4">{legend}</div>}
          {children}
        </>
      ) : (
        table
      )}
      <div className="mt-5 flex gap-2 border-t border-border pt-4 text-sm text-ink-2">
        <Info aria-hidden className="mt-0.5 size-4 shrink-0 text-muted" />
        <p>
          <span className="font-medium text-ink">How to read this. </span>
          {howToRead}
        </p>
      </div>
    </Card>
  );
}
