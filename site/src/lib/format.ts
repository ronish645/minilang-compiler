export const pct = (value: number | null | undefined, digits = 0) =>
  value == null ? "–" : `${(value * 100).toFixed(digits)}%`;

export const usd = (value: number | null | undefined) => {
  if (value == null) return "–";
  if (value === 0) return "$0";
  if (value < 0.01) return `$${value.toFixed(4)}`;
  return `$${value.toFixed(2)}`;
};

export const seconds = (value: number) => `${value.toFixed(1)}s`;

export const count = (value: number) => value.toLocaleString("en-US");

export const fraction = (hits: number, total: number) => `${hits}/${total}`;
