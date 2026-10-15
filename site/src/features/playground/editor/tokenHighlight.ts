// Highlights one token in the editor while its row is hovered in the Tokens tab.
import { StateEffect, StateField } from "@codemirror/state";
import { Decoration, EditorView, type DecorationSet } from "@codemirror/view";

export const setHighlight = StateEffect.define<{ from: number; to: number } | null>();

const highlightMark = Decoration.mark({ class: "cm-token-highlight" });

export const tokenHighlight = StateField.define<DecorationSet>({
  create: () => Decoration.none,
  update(value, tr) {
    for (const effect of tr.effects) {
      if (!effect.is(setHighlight)) continue;
      const range = effect.value;
      return range && range.to > range.from
        ? Decoration.set([highlightMark.range(range.from, range.to)])
        : Decoration.none;
    }
    return value.map(tr.changes);
  },
  provide: (field) => EditorView.decorations.from(field),
});
