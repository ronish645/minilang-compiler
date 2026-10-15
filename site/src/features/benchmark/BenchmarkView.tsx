import { Container } from "../../components/layout/Page";
import type { Summary } from "../../lib/types";
import { RunOverview } from "./layout/RunOverview";
import { SectionNav } from "./layout/SectionNav";
import { useScrollSpy } from "./layout/useScrollSpy";
import { runShortLabel } from "../../lib/runs";
import { SECTION_IDS } from "./lib/sections";
import { MethodSection } from "./method/MethodSection";
import { CostSection } from "./sections/CostSection";
import { ErrorsSection } from "./sections/ErrorsSection";
import { HeatmapSection } from "./sections/HeatmapSection";
import { OutcomesSection } from "./sections/OutcomesSection";
import { RepairSection } from "./sections/RepairSection";
import { TestingSection } from "./sections/TestingSection";
import { TiersSection } from "./sections/TiersSection";

interface BenchmarkViewProps {
  summary: Summary;
  runId: string;
  onRunChange: (runId: string) => void;
  onSection: (id: string) => void;
}

/** The analysis for one run: run picker and headline tiles, then the sections. */
export function BenchmarkView({ summary, runId, onRunChange, onSection }: BenchmarkViewProps) {
  const active = useScrollSpy(SECTION_IDS, runId);
  const run = summary.runs.find((r) => r.id === runId);
  const runLabel = run ? runShortLabel(run) : runId;
  const props = { summary, runId };

  return (
    <Container className="py-8 sm:py-10">
      <RunOverview summary={summary} runId={runId} onRunChange={onRunChange} />
      <div className="mt-8 lg:mt-12 lg:grid lg:grid-cols-[11rem_minmax(0,1fr)] lg:gap-10">
        <SectionNav active={active} onSelect={onSection} runLabel={runLabel} />
        {/* key: switching runs remounts the sections, resetting per-chart view toggles and pickers */}
        <div key={runId} className="mt-8 flex min-w-0 flex-col gap-16 lg:mt-0 lg:gap-20">
          <HeatmapSection {...props} />
          <OutcomesSection {...props} />
          <RepairSection {...props} />
          <TestingSection {...props} />
          <CostSection {...props} />
          <TiersSection {...props} onRunChange={onRunChange} />
          <ErrorsSection {...props} />
          <MethodSection summary={summary} />
        </div>
      </div>
    </Container>
  );
}
