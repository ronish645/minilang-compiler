import type { ReactNode } from "react";
import { cn } from "../../../lib/cn";

export interface Column<Row> {
  key: string;
  header: string;
  numeric?: boolean;
  render: (row: Row) => ReactNode;
}

interface DataTableProps<Row> {
  caption: string;
  columns: Column<Row>[];
  rows: Row[];
  rowKey: (row: Row) => string;
}

/** The accessible twin of every chart: the same numbers in a plain table. */
export function DataTable<Row>({ caption, columns, rows, rowKey }: DataTableProps<Row>) {
  return (
    <div className="overflow-x-auto rounded-xl ring-1 ring-inset ring-border">
      <table className="w-full min-w-max border-collapse text-sm">
        <caption className="sr-only">{caption}</caption>
        <thead>
          <tr className="bg-surface-2 text-left text-xs text-ink-2">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn("px-3 py-2 font-medium", column.numeric && "text-right")}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={rowKey(row)} className="border-t border-border">
              {columns.map((column, index) => {
                const Cell = index === 0 ? "th" : "td";
                return (
                  <Cell
                    key={column.key}
                    scope={index === 0 ? "row" : undefined}
                    className={cn(
                      "px-3 py-2 text-left font-normal text-ink",
                      column.numeric && "text-right tabular-nums",
                    )}
                  >
                    {column.render(row)}
                  </Cell>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
