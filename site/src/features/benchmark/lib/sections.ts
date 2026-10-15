import type { Summary } from "../../../lib/types";

// Section ids are shared with the Overview page: /benchmark?section=<id>.
export const SECTIONS = [
  { id: "heatmap", label: "Pass rate" },
  { id: "outcomes", label: "How models fail" },
  { id: "repair", label: "Error messages" },
  { id: "testing", label: "Testing habits" },
  { id: "cost", label: "Cost per solve" },
  { id: "tiers", label: "Task tiers" },
  { id: "errors", label: "Common errors" },
  { id: "method", label: "Methodology" },
] as const;

export type SectionId = (typeof SECTIONS)[number]["id"];

export const SECTION_IDS: readonly string[] = SECTIONS.map((section) => section.id);

/** Every analysis section renders one run of the summary. */
export interface SectionProps {
  summary: Summary;
  runId: string;
}
