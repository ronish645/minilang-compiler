import { ExternalLink, Wrench } from "lucide-react";
import { Badge } from "../../../components/ui/Badge";
import { buttonClasses } from "../../../components/ui/Button";
import { Card, CardHeader } from "../../../components/ui/Card";
import { cn } from "../../../lib/cn";
import { BENCH_URL } from "../../../lib/links";
import { CONDITION_ORDER } from "../../../lib/models";
import type { Summary } from "../../../lib/types";
import { BenchmarkSection } from "../layout/BenchmarkSection";
import { AgentLoopDiagram } from "./AgentLoopDiagram";
import { LIMITATIONS, METRICS, TIERS } from "./methodContent";

function Conditions({ summary }: { summary: Summary }) {
  const conditions = [...summary.conditions].sort(
    (a, b) => CONDITION_ORDER.indexOf(a.id as never) - CONDITION_ORDER.indexOf(b.id as never),
  );
  return (
    <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {conditions.map((condition) => (
        <li key={condition.id} className="rounded-xl border border-border p-3">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-semibold text-ink">{condition.label}</span>
            <code className="font-mono text-xs text-muted">{condition.id}</code>
            {condition.uses_tools ? (
              <Badge tone="accent" icon={<Wrench aria-hidden className="size-3" />}>
                Tools
              </Badge>
            ) : (
              <Badge>No tools</Badge>
            )}
          </div>
          <p className="mt-1.5 text-sm text-ink-2">{condition.description}</p>
        </li>
      ))}
    </ul>
  );
}

function Tiers() {
  return (
    <ul className="divide-y divide-border">
      {TIERS.map((tier) => (
        <li key={tier.tier} className="grid grid-cols-[4.5rem_minmax(0,1fr)] gap-3 py-2.5 text-sm">
          <span className="font-medium text-ink">
            Tier {tier.tier}
            <span className="block text-xs font-normal tabular-nums text-muted">{tier.tasks} tasks</span>
          </span>
          <span className="text-ink-2">{tier.what}</span>
        </li>
      ))}
    </ul>
  );
}

export function MethodSection({ summary }: { summary: Summary }) {
  return (
    <BenchmarkSection
      id="method"
      eyebrow="Methodology"
      title="How the benchmark works"
      takeaway="MiniLang was written for this project, so no model has seen it in training. Each model learns it from the spec in its prompt, then writes programs through a compiler-as-tool loop."
    >
      <div className="flex flex-col gap-4">
        <Card>
          <CardHeader title="One episode" subtitle="What happens between the prompt and the grade." />
          <AgentLoopDiagram />
        </Card>

        <Card>
          <CardHeader
            title="Five feedback conditions"
            subtitle="The experimental variable: what the model sees when its code fails. Successful runs look the same in every condition."
          />
          <Conditions summary={summary} />
        </Card>

        <div className="grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader title="Task tiers" subtitle="Tiers 1–4 ran on spec v1; tier 5 on spec v2.1." />
            <Tiers />
          </Card>
          <Card>
            <CardHeader title="Metrics" />
            <dl className="flex flex-col gap-3 text-sm">
              {METRICS.map((metric) => (
                <div key={metric.term}>
                  <dt className="font-medium text-ink">{metric.term}</dt>
                  <dd className="mt-0.5 text-ink-2">{metric.definition}</dd>
                </div>
              ))}
            </dl>
          </Card>
        </div>

        <Card>
          <CardHeader title="Limitations" subtitle="What these results can and can't tell you." />
          <ul className="flex list-disc flex-col gap-2 pl-5 text-sm text-ink-2 marker:text-muted">
            {LIMITATIONS.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <a
            href={BENCH_URL}
            target="_blank"
            rel="noreferrer"
            className={cn(buttonClasses("secondary", "sm"), "mt-5")}
          >
            Benchmark code and full reports
            <ExternalLink aria-hidden className="size-3.5" />
          </a>
        </Card>
      </div>
    </BenchmarkSection>
  );
}
