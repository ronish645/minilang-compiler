import type { KeyboardEvent } from "react";

/**
 * Arrow-key handling for a row of options (tabs, radio groups): Left/Right and
 * Home/End move to and select another option, so the group is one Tab stop.
 */
export function rovingKeyDown<T>(
  event: KeyboardEvent<HTMLElement>,
  values: readonly T[],
  current: T,
  select: (value: T) => void,
) {
  const index = values.indexOf(current);
  const last = values.length - 1;
  const next =
    event.key === "ArrowRight" || event.key === "ArrowDown"
      ? (index + 1) % values.length
      : event.key === "ArrowLeft" || event.key === "ArrowUp"
        ? (index - 1 + values.length) % values.length
        : event.key === "Home"
          ? 0
          : event.key === "End"
            ? last
            : null;
  if (next === null) return;
  event.preventDefault();
  select(values[next]);
  const buttons = event.currentTarget.querySelectorAll<HTMLElement>("[data-roving]");
  buttons[next]?.focus();
}
