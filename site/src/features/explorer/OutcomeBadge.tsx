import { Ban, CircleCheck, CircleX, Clock, FileX, TriangleAlert, type LucideIcon } from "lucide-react";
import { Badge } from "../../components/ui/Badge";
import { OUTCOME_LABEL } from "../../lib/models";
import type { Outcome } from "../../lib/types";

type Tone = "good" | "critical" | "warning" | "neutral";

const STYLE: Record<Outcome, { tone: Tone; icon: LucideIcon }> = {
  passed: { tone: "good", icon: CircleCheck },
  wrong_output: { tone: "critical", icon: CircleX },
  compile_error: { tone: "critical", icon: CircleX },
  runtime_error: { tone: "critical", icon: TriangleAlert },
  no_code: { tone: "neutral", icon: FileX },
  refusal: { tone: "neutral", icon: Ban },
  turn_limit: { tone: "warning", icon: Clock },
  api_error: { tone: "neutral", icon: TriangleAlert },
};

/** Outcome as text plus an icon, so it never depends on color alone. */
export function OutcomeBadge({ outcome }: { outcome: Outcome }) {
  const { tone, icon: Icon } = STYLE[outcome] ?? STYLE.api_error;
  return (
    <Badge tone={tone} icon={<Icon className="size-3.5" aria-hidden />} className="whitespace-nowrap">
      {OUTCOME_LABEL[outcome] ?? outcome}
    </Badge>
  );
}
