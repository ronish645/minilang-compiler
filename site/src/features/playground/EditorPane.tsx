import type { Token } from "./worker/protocol";
import { CodeEditor } from "./editor/CodeEditor";
import type { EditorMarker } from "./editor/errorMarkers";
import { EditorToolbar, RUN_SHORTCUT, type ShareState } from "./EditorToolbar";
import type { Example } from "./examples";

interface EditorPaneProps {
  source: string;
  onChange: (source: string) => void;
  markers: EditorMarker[];
  highlightedToken: Token | null;
  exampleId: string;
  example: Example | null;
  isModified: boolean;
  onPickExample: (id: string) => void;
  onRun: () => void;
  onReset: () => void;
  onShare: () => void;
  shareState: ShareState;
}

/** Toolbar, editor and a one-line footer describing the loaded program. */
export function EditorPane(props: EditorPaneProps) {
  const { example, isModified } = props;
  const lines = props.source.split("\n").length;
  return (
    <section
      aria-label="Editor"
      className="flex min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-surface shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
    >
      <EditorToolbar
        exampleId={props.exampleId}
        onPickExample={props.onPickExample}
        onRun={props.onRun}
        onReset={props.onReset}
        onShare={props.onShare}
        shareState={props.shareState}
        canReset={isModified}
      />
      <div className="h-[420px] min-h-0 sm:h-[480px] lg:h-auto lg:flex-1">
        <CodeEditor
          value={props.source}
          onChange={props.onChange}
          onRun={props.onRun}
          markers={props.markers}
          highlightedToken={props.highlightedToken}
        />
      </div>
      <footer className="flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-border px-3 py-2 text-xs text-muted">
        <span className="min-w-0 truncate">
          {example ? example.blurb : "A program loaded from a shared link."}
          {isModified && <span className="ml-1.5 text-ink-2">· edited</span>}
        </span>
        <span className="ml-auto shrink-0 tabular-nums">
          {lines} {lines === 1 ? "line" : "lines"} · checks as you type · {RUN_SHORTCUT} to run
        </span>
      </footer>
    </section>
  );
}
