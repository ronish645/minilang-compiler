import { javascript } from "@codemirror/lang-javascript";
import { Prec, type EditorState } from "@codemirror/state";
import { EditorView, keymap } from "@codemirror/view";
import CodeMirror, { type ReactCodeMirrorRef } from "@uiw/react-codemirror";
import { useEffect, useMemo, useRef } from "react";
import type { Token } from "../worker/protocol";
import { editorTheme } from "./editorTheme";
import { errorMarkers, rangeAt, setMarkers, type EditorMarker } from "./errorMarkers";
import { setHighlight, tokenHighlight } from "./tokenHighlight";

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  onRun: () => void;
  markers: EditorMarker[];
  highlightedToken: Token | null;
}

/** Source range of a token. Strings are scanned to their closing quote (escapes change the length). */
function tokenRange(state: EditorState, token: Token) {
  const start = rangeAt(state, token.line, token.col);
  if (!start) return null;
  if (token.type !== "STRING") return { from: start.from, to: start.from + Math.max(token.value.length, 1) };
  const line = state.doc.lineAt(start.from);
  const text = state.doc.sliceString(start.from, line.to);
  const quote = text[0];
  let end = 1;
  while (end < text.length && text[end] !== quote) end += text[end] === "\\" ? 2 : 1;
  return { from: start.from, to: start.from + Math.min(end + 1, text.length) };
}

export function CodeEditor({ value, onChange, onRun, markers, highlightedToken }: CodeEditorProps) {
  const ref = useRef<ReactCodeMirrorRef>(null);
  const onRunRef = useRef(onRun);
  useEffect(() => {
    onRunRef.current = onRun;
  }, [onRun]);

  // Built once: handlers reach the latest callbacks through refs.
  const extensions = useMemo(
    () => [
      javascript(),
      editorTheme,
      errorMarkers,
      tokenHighlight,
      EditorView.contentAttributes.of({ "aria-label": "MiniLang source code" }),
      Prec.highest(
        keymap.of([
          {
            key: "Mod-Enter",
            run: () => {
              onRunRef.current();
              return true;
            },
          },
        ]),
      ),
    ],
    [],
  );

  // Push compiler errors into the editor whenever they change.
  useEffect(() => {
    ref.current?.view?.dispatch({ effects: setMarkers.of(markers) });
  }, [markers]);

  useEffect(() => {
    const view = ref.current?.view;
    if (!view) return;
    const range = highlightedToken ? tokenRange(view.state, highlightedToken) : null;
    view.dispatch({ effects: setHighlight.of(range) });
  }, [highlightedToken]);

  return (
    <CodeMirror
      ref={ref}
      value={value}
      onChange={onChange}
      onCreateEditor={(view) => view.dispatch({ effects: setMarkers.of(markers) })}
      extensions={extensions}
      theme="none"
      height="100%"
      className="h-full min-h-0 overflow-hidden"
      basicSetup={{
        lineNumbers: true,
        foldGutter: true,
        highlightActiveLine: true,
        autocompletion: false,
        searchKeymap: true,
      }}
    />
  );
}
