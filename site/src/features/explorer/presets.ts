// Featured shortcuts: each is just a set of filters, so it shares the URL
// format with the filter bar and can be refined after clicking it.
import { DEFAULT_FILTERS, FAILED, filtersKey, type Filters } from "./filters";

export interface Preset {
  id: string;
  label: string;
  description: string;
  filters: Filters;
}

const preset = (id: string, label: string, description: string, partial: Partial<Filters>): Preset => ({
  id,
  label,
  description,
  filters: { ...DEFAULT_FILTERS, ...partial },
});

export const PRESETS: Preset[] = [
  preset("qwen-failures", "Qwen's failures", "Every episode the local 3B model failed", {
    model: "qwen-3b-local",
    outcome: FAILED,
  }),
  preset("untested", "Sonnet's untested submissions", "Failed without ever running the code", {
    model: "claude-sonnet",
    preset: "untested",
  }),
  preset("repairs", "Every repair", "The first run failed, the submission passed", {
    preset: "repairs",
  }),
  preset("hints", "Fix-it hints", "The tier-5 condition with compiler hints", {
    run: "v21-tier5",
    condition: "hint",
  }),
];

export const activePreset = (filters: Filters) =>
  PRESETS.find((item) => filtersKey(item.filters) === filtersKey(filters))?.id ?? null;
