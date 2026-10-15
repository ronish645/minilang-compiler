// A CodeMirror theme built only from the site's CSS variables, so the editor
// follows light/dark mode without being rebuilt.
import { HighlightStyle, syntaxHighlighting } from "@codemirror/language";
import { EditorView } from "@codemirror/view";
import { tags as t } from "@lezer/highlight";

const chrome = EditorView.theme({
  "&": {
    color: "var(--ink)",
    backgroundColor: "var(--surface)",
    fontSize: "13.5px",
    height: "100%",
  },
  "&.cm-focused": { outline: "none" },
  ".cm-scroller": {
    fontFamily: "var(--font-mono)",
    lineHeight: "1.65",
    fontVariantLigatures: "none",
  },
  ".cm-content": { caretColor: "var(--accent)", padding: "12px 0" },
  ".cm-cursor, .cm-dropCursor": { borderLeftColor: "var(--accent)", borderLeftWidth: "2px" },
  "&.cm-focused > .cm-scroller > .cm-selectionLayer .cm-selectionBackground, .cm-selectionBackground, .cm-content ::selection":
    { backgroundColor: "var(--accent-soft)" },
  ".cm-gutters": {
    backgroundColor: "var(--surface)",
    color: "var(--muted)",
    border: "none",
    borderRight: "1px solid var(--border)",
  },
  ".cm-lineNumbers .cm-gutterElement": { padding: "0 10px 0 14px", minWidth: "36px" },
  ".cm-activeLine": { backgroundColor: "color-mix(in srgb, var(--surface-2) 70%, transparent)" },
  ".cm-activeLineGutter": { backgroundColor: "transparent", color: "var(--ink-2)" },
  ".cm-matchingBracket, &.cm-focused .cm-matchingBracket": {
    backgroundColor: "var(--surface-3)",
    outline: "1px solid var(--border-strong)",
  },
  ".cm-foldGutter .cm-gutterElement": { color: "var(--muted)" },
  ".cm-tooltip": {
    backgroundColor: "var(--surface)",
    border: "1px solid var(--border-strong)",
    borderRadius: "8px",
    color: "var(--ink)",
  },
  ".cm-tooltip-autocomplete > ul > li[aria-selected]": {
    backgroundColor: "var(--accent-soft)",
    color: "var(--ink)",
  },
  // Error markers (see errorMarkers.ts).
  ".cm-error-mark": {
    textDecoration: "underline wavy var(--critical)",
    textDecorationSkipInk: "none",
    textUnderlineOffset: "3px",
    backgroundColor: "color-mix(in srgb, var(--critical) 10%, transparent)",
    borderRadius: "2px",
  },
  ".cm-error-line": { backgroundColor: "color-mix(in srgb, var(--critical) 6%, transparent)" },
  ".cm-error-gutter": { width: "16px", paddingLeft: "4px" },
  ".cm-error-dot": {
    display: "block",
    width: "7px",
    height: "7px",
    marginTop: "8px",
    borderRadius: "9999px",
    backgroundColor: "var(--critical)",
    cursor: "help",
  },
  ".cm-token-highlight": {
    backgroundColor: "color-mix(in srgb, var(--accent) 22%, transparent)",
    outline: "1px solid var(--accent)",
    borderRadius: "2px",
  },
});

const highlight = HighlightStyle.define([
  { tag: [t.keyword, t.controlKeyword, t.definitionKeyword, t.moduleKeyword], color: "var(--accent-ink)", fontWeight: "500" },
  { tag: [t.string, t.special(t.string)], color: "var(--good)" },
  { tag: [t.number, t.bool, t.null, t.atom], color: "var(--series-2)" },
  { tag: [t.lineComment, t.blockComment, t.comment], color: "var(--muted)", fontStyle: "italic" },
  { tag: [t.function(t.variableName), t.function(t.definition(t.variableName))], color: "var(--series-5)" },
  { tag: [t.operator, t.punctuation, t.bracket], color: "var(--ink-2)" },
  { tag: t.variableName, color: "var(--ink)" },
  { tag: t.invalid, color: "var(--critical)" },
]);

export const editorTheme = [chrome, syntaxHighlighting(highlight)];
