import { ArrowRight, Coins, FlaskConical, MessageSquareText, Send, type LucideIcon } from "lucide-react";
import { Link } from "react-router-dom";
import type { Summary } from "../../../lib/types";
import { buildFindings, findingHref, type FindingSection } from "../findings";

const ICONS: Record<FindingSection, LucideIcon> = {
  heatmap: FlaskConical,
  repair: MessageSquareText,
  testing: Send,
  cost: Coins,
};

export function KeyFindings({ summary }: { summary: Summary }) {
  const findings = buildFindings(summary);
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {findings.map((finding) => {
        const Icon = ICONS[finding.section];
        return (
          <Link
            key={finding.section}
            to={findingHref(finding)}
            className="group flex flex-col rounded-2xl border border-border bg-surface p-5 shadow-[0_1px_2px_rgba(0,0,0,0.04)] transition hover:border-border-strong hover:shadow-md sm:p-6"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-4xl font-semibold tracking-tight text-ink tabular-nums sm:text-5xl">
                  {finding.figure}
                </p>
                <p className="mt-1 text-sm text-muted">{finding.figureLabel}</p>
              </div>
              <span className="grid size-9 shrink-0 place-items-center rounded-xl bg-surface-2 text-ink-2">
                <Icon className="size-4" aria-hidden />
              </span>
            </div>
            <h3 className="mt-5 text-lg font-semibold tracking-tight text-ink">{finding.title}</h3>
            <p className="mt-1.5 flex-1 text-sm leading-relaxed text-ink-2">{finding.body}</p>
            <span className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-accent-ink">
              {finding.linkLabel}
              <ArrowRight className="size-4 transition group-hover:translate-x-0.5" aria-hidden />
            </span>
          </Link>
        );
      })}
    </div>
  );
}
