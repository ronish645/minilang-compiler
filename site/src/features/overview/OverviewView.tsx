import type { ReactNode } from "react";
import { Container } from "../../components/layout/Page";
import { SectionHeading } from "../../components/ui/SectionHeading";
import { ErrorState, Skeleton } from "../../components/ui/StateViews";
import { useSummary } from "../../lib/data";
import type { Summary } from "../../lib/types";
import { BuiltWith } from "./sections/BuiltWith";
import { EpisodeFlow } from "./sections/EpisodeFlow";
import { HeroSection } from "./sections/HeroSection";
import { KeyFindings } from "./sections/KeyFindings";
import { PipelineDiagram } from "./sections/PipelineDiagram";
import { RepoCards } from "./sections/RepoCards";
import { StatsRow } from "./sections/StatsRow";

interface SectionProps {
  id: string;
  eyebrow: string;
  title: string;
  description?: ReactNode;
  children: ReactNode;
}

function Section({ id, eyebrow, title, description, children }: SectionProps) {
  return (
    <section aria-labelledby={id} className="py-14 sm:py-20">
      <SectionHeading id={id} eyebrow={eyebrow} title={title} description={description} />
      <div className="mt-8 sm:mt-10">{children}</div>
    </section>
  );
}

/** Data-driven parts wait for summary.json; the static story renders at once. */
function WithSummary({ render }: { render: (summary: Summary) => ReactNode }) {
  const summary = useSummary();
  if (summary.status === "error") return <ErrorState message={summary.message} />;
  if (summary.status === "loading") return <Skeleton className="h-40 w-full" />;
  return <>{render(summary.data)}</>;
}

export function OverviewView() {
  return (
    <>
      <HeroSection />
      <Container>
        <div className="-mt-px pt-10 sm:pt-12">
          <WithSummary render={(summary) => <StatsRow summary={summary} />} />
        </div>

        <Section
          id="findings-title"
          eyebrow="Key findings"
          title="What the benchmark showed"
          description="Every number below is computed from the published results. Each card links to the chart behind it."
        >
          <WithSummary render={(summary) => <KeyFindings summary={summary} />} />
        </Section>

        <Section
          id="pipeline-title"
          eyebrow="The compiler"
          title="Five stages, written from scratch"
          description="No parser generators and no runtime dependencies. Every stage is a small Python module with its own tests."
        >
          <PipelineDiagram />
        </Section>

        <Section
          id="episode-title"
          eyebrow="The benchmark"
          title="How an episode works"
          description="Each model gets the spec and a task, uses the compiler as a tool, and submits a program that is graded by its exact output."
        >
          <WithSummary render={(summary) => <EpisodeFlow summary={summary} />} />
        </Section>

        <Section id="repo-title" eyebrow="What's in the repo" title="Three parts, one codebase">
          <WithSummary render={(summary) => <RepoCards summary={summary} />} />
        </Section>

        <div className="pb-16 sm:pb-24">
          <BuiltWith />
        </div>
      </Container>
    </>
  );
}
