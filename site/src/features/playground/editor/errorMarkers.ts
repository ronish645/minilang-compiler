// Inline diagnostics without @codemirror/lint: a StateField holds a squiggle
// under each error position, a tinted line, and a dot in a custom gutter.
// The page pushes new markers with an effect after every compile.
import { RangeSet, StateEffect, StateField, type EditorState, type Range } from "@codemirror/state";
import { Decoration, EditorView, GutterMarker, gutter, type DecorationSet } from "@codemirror/view";

export interface EditorMarker {
  line: number; // 1-based, as the compiler reports it
  col: number; // 1-based
  message: string;
}

export const setMarkers = StateEffect.define<EditorMarker[]>();

class ErrorDot extends GutterMarker {
  constructor(readonly message: string) {
    super();
  }
  eq(other: ErrorDot) {
    return other.message === this.message;
  }
  toDOM() {
    const dot = document.createElement("span");
    dot.className = "cm-error-dot";
    dot.title = this.message;
    return dot;
  }
}

const WORD = /[\w$]/;

/** The range to underline: the word at (line, col), or one character. */
export function rangeAt(state: EditorState, line: number, col: number): { from: number; to: number } | null {
  if (line < 1 || line > state.doc.lines) return null;
  const text = state.doc.line(line);
  let from = Math.min(text.from + Math.max(col - 1, 0), text.to);
  if (from === text.to && from > text.from) from -= 1; // an error at end of line marks the last char
  let to = from;
  while (to < text.to && WORD.test(state.doc.sliceString(to, to + 1))) to++;
  return { from, to: Math.max(to, Math.min(from + 1, text.to)) };
}

interface MarkerState {
  decorations: DecorationSet;
  dots: RangeSet<GutterMarker>;
}

function build(state: EditorState, markers: EditorMarker[]): MarkerState {
  const marks: Range<Decoration>[] = [];
  const dots: Range<GutterMarker>[] = [];
  const seenLines = new Set<number>();
  for (const marker of markers) {
    const range = rangeAt(state, marker.line, marker.col);
    if (!range) continue;
    const lineStart = state.doc.line(marker.line).from;
    if (range.to > range.from) {
      marks.push(Decoration.mark({ class: "cm-error-mark", attributes: { title: marker.message } }).range(range.from, range.to));
    }
    if (!seenLines.has(marker.line)) {
      seenLines.add(marker.line);
      marks.push(Decoration.line({ class: "cm-error-line" }).range(lineStart));
      dots.push(new ErrorDot(marker.message).range(lineStart));
    }
  }
  return { decorations: Decoration.set(marks, true), dots: RangeSet.of(dots, true) };
}

const markerField = StateField.define<MarkerState>({
  create: () => ({ decorations: Decoration.none, dots: RangeSet.empty }),
  update(value, tr) {
    for (const effect of tr.effects) if (effect.is(setMarkers)) return build(tr.state, effect.value);
    if (!tr.docChanged) return value;
    return { decorations: value.decorations.map(tr.changes), dots: value.dots.map(tr.changes) };
  },
  provide: (field) => EditorView.decorations.from(field, (v) => v.decorations),
});

export const errorMarkers = [
  markerField,
  gutter({
    class: "cm-error-gutter",
    markers: (view) => view.state.field(markerField).dots,
  }),
];
