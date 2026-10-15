import { useCallback, useState } from "react";
import { Container, PageHeader } from "../components/layout/Page";
import { EditorPane } from "../features/playground/EditorPane";
import { HowItWorks } from "../features/playground/HowItWorks";
import { InspectorPane } from "../features/playground/InspectorPane";
import { usePlayground } from "../features/playground/usePlayground";
import type { ExploreResult, Token } from "../features/playground/worker/protocol";

export default function PlaygroundPage() {
  const pg = usePlayground();
  // Remember which result the hovered token came from, so a new compile drops a stale highlight.
  const [hover, setHover] = useState<{ token: Token; result: ExploreResult } | null>(null);
  const result = pg.compiler.result;
  const hoveredToken = hover && hover.result === result ? hover.token : null;
  const onHoverToken = useCallback(
    (token: Token | null) => setHover(token && result ? { token, result } : null),
    [result],
  );

  return (
    <>
      <PageHeader
        eyebrow="Playground"
        title="Run the compiler in your browser"
        description="This is the real Python compiler, running locally through WebAssembly. No server. Edit the code and watch every stage update."
      />
      <Container className="py-6 lg:py-8 [&_:is(pre,code,kbd,.font-mono)]:[font-variant-ligatures:none]">
        <div className="grid grid-cols-[minmax(0,1fr)] gap-4 lg:h-[calc(100vh-7rem)] lg:min-h-[640px] lg:max-h-[960px] lg:grid-cols-[minmax(0,1.05fr)_minmax(0,1fr)]">
          <EditorPane
            source={pg.source}
            onChange={pg.setSource}
            markers={pg.markers}
            highlightedToken={hoveredToken}
            exampleId={pg.exampleId}
            example={pg.example}
            isModified={pg.isModified}
            onPickExample={pg.pickExample}
            onRun={pg.run}
            onReset={pg.reset}
            onShare={pg.share}
            shareState={pg.shareState}
          />
          <InspectorPane
            compiler={pg.compiler}
            onRetry={pg.compiler.retry}
            tab={pg.tab}
            onTabChange={pg.setTab}
            onHoverToken={onHoverToken}
          />
        </div>
        <HowItWorks />
      </Container>
    </>
  );
}
