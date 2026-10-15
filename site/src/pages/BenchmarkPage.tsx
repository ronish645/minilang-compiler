import { Container, PageHeader } from "../components/layout/Page";
import { ErrorState, LoadingState } from "../components/ui/StateViews";
import { BenchmarkView } from "../features/benchmark/BenchmarkView";
import { useBenchmarkParams } from "../features/benchmark/layout/useBenchmarkParams";
import { runsNewestFirst } from "../features/benchmark/lib/derive";
import { useSummary } from "../lib/data";

export default function BenchmarkPage() {
  const state = useSummary();
  const summary = state.status === "ready" ? state.data : undefined;
  const newest = summary ? runsNewestFirst(summary)[0]?.id : undefined;
  const { runParam, setRun, goToSection } = useBenchmarkParams(summary !== undefined);
  const runId = summary?.runs.some((run) => run.id === runParam) ? runParam : newest;

  return (
    <>
      <PageHeader
        eyebrow="Benchmark"
        title="Can LLMs learn a language they've never seen?"
        description="Five models learned MiniLang from its spec alone, then wrote programs through a compiler-as-tool loop under five kinds of error feedback. Here is what passed, what failed, and why."
      />
      {state.status === "loading" && <LoadingState label="Loading benchmark results…" />}
      {state.status === "error" && (
        <Container className="py-10">
          <ErrorState message={state.message} />
        </Container>
      )}
      {summary && runId && (
        <BenchmarkView summary={summary} runId={runId} onRunChange={setRun} onSection={goToSection} />
      )}
    </>
  );
}
