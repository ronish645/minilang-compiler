import type { ErrorPattern } from "../../../lib/types";
import { ERROR_HABITS } from "../lib/errorHabits";

/** Plain-English readings for the top error patterns: the habit, an example and the MiniLang fix. */
export function HabitList({ patterns }: { patterns: ErrorPattern[] }) {
  const explained = patterns.filter((row) => ERROR_HABITS[row.pattern]);
  if (explained.length === 0) return null;

  return (
    <div className="mt-6">
      <h4 className="text-sm font-semibold text-ink">Likely habits behind the top errors</h4>
      <ol className="mt-3 grid gap-3 md:grid-cols-3">
        {explained.map((row) => {
          const habit = ERROR_HABITS[row.pattern];
          return (
            <li key={row.pattern} className="rounded-xl bg-surface-2 p-3 text-sm">
              <code className="block break-words font-mono text-xs text-ink">{row.pattern}</code>
              <p className="mt-2 text-ink-2">{habit.habit}</p>
              {habit.example && (
                <dl className="mt-2 grid grid-cols-[auto_minmax(0,1fr)] gap-x-2 gap-y-1 text-xs">
                  <dt className="text-muted">Typical</dt>
                  <dd>
                    <code className="break-words rounded bg-surface px-1 font-mono text-ink">{habit.example}</code>
                  </dd>
                  {habit.fix && (
                    <>
                      <dt className="text-muted">MiniLang</dt>
                      <dd>
                        <code className="break-words rounded bg-surface px-1 font-mono text-ink">{habit.fix}</code>
                      </dd>
                    </>
                  )}
                </dl>
              )}
            </li>
          );
        })}
      </ol>
    </div>
  );
}
