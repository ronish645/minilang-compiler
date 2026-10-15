import { Ban, Bug, CircleCheck, CircleDashed, CircleX, TriangleAlert, type LucideIcon } from "lucide-react";
import type { Outcome } from "../../../lib/types";

// Outcome is a *state*, not an identity, and the categorical slots already mean
// "which model" on this page. So outcomes wear the reserved status scale,
// ordered by how far the program got: passed (good) -> ran but printed the wrong
// thing (warning) -> crashed while running (serious) -> never compiled
// (critical). "No code" and rarer outcomes are neutral grays: there was no
// program to judge. Every status color ships with an icon and a label.

export interface OutcomeStyle {
  key: string;
  label: string;
  color: string;
  icon: LucideIcon;
  outcomes: Outcome[];
}

export const OUTCOME_STYLES: OutcomeStyle[] = [
  { key: "passed", label: "Passed", color: "var(--good-mark)", icon: CircleCheck, outcomes: ["passed"] },
  {
    key: "wrong_output",
    label: "Wrong output",
    color: "var(--warning)",
    icon: CircleX,
    outcomes: ["wrong_output"],
  },
  {
    key: "runtime_error",
    label: "Runtime error",
    color: "var(--serious)",
    icon: Bug,
    outcomes: ["runtime_error"],
  },
  {
    key: "compile_error",
    label: "Compile error",
    color: "var(--critical)",
    icon: TriangleAlert,
    outcomes: ["compile_error"],
  },
  { key: "no_code", label: "No code", color: "var(--muted)", icon: CircleDashed, outcomes: ["no_code"] },
  {
    key: "other",
    label: "Other (refusal, turn limit, API error)",
    color: "var(--axis)",
    icon: Ban,
    outcomes: ["refusal", "turn_limit", "api_error"],
  },
];

export const outcomeCount = (
  outcomes: Partial<Record<Outcome, number>>,
  style: OutcomeStyle,
): number => style.outcomes.reduce((sum, outcome) => sum + (outcomes[outcome] ?? 0), 0);
