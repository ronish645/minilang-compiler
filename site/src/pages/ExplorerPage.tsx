import { PageHeader } from "../components/layout/Page";
import { ExplorerView } from "../features/explorer/ExplorerView";

export default function ExplorerPage() {
  return (
    <>
      <PageHeader
        eyebrow="Episodes"
        title="Every graded run, inspectable"
        description="These are the exact programs the models submitted, with each run's result and the graded output. Filter, search, and open any episode."
      />
      <ExplorerView />
    </>
  );
}
