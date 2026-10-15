import { Check, Link2, Play, RotateCcw } from "lucide-react";
import { Button } from "../../components/ui/Button";
import { ExamplePicker } from "./ExamplePicker";

export type ShareState = "idle" | "copied" | "too-long" | "failed";

const SHARE_LABEL: Record<ShareState, string> = {
  idle: "Copy link",
  copied: "Copied",
  "too-long": "Too long to share",
  failed: "Copy failed",
};

const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.userAgent);
export const RUN_SHORTCUT = isMac ? "⌘ ↵" : "Ctrl ↵";

interface EditorToolbarProps {
  exampleId: string;
  onPickExample: (id: string) => void;
  onRun: () => void;
  onReset: () => void;
  onShare: () => void;
  shareState: ShareState;
  canReset: boolean;
}

export function EditorToolbar(props: EditorToolbarProps) {
  const { exampleId, onPickExample, onRun, onReset, onShare, shareState, canReset } = props;
  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-border px-3 py-2.5">
      <ExamplePicker value={exampleId} onChange={onPickExample} />
      <div className="ml-auto flex items-center gap-1">
        <Button
          size="sm"
          variant="ghost"
          onClick={onReset}
          disabled={!canReset}
          icon={<RotateCcw className="size-3.5" aria-hidden />}
          title="Restore the original program"
          aria-label="Reset to the original program"
        >
          <span className="hidden sm:inline">Reset</span>
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={onShare}
          icon={
            shareState === "copied" ? (
              <Check className="size-3.5 text-good" aria-hidden />
            ) : (
              <Link2 className="size-3.5" aria-hidden />
            )
          }
        >
          <span aria-live="polite">{SHARE_LABEL[shareState]}</span>
        </Button>
        <Button size="sm" variant="primary" onClick={onRun} icon={<Play className="size-3.5" aria-hidden />}>
          Run
          <kbd className="ml-1 hidden rounded bg-white/20 px-1.5 py-px font-mono text-[10.5px] sm:inline">
            {RUN_SHORTCUT}
          </kbd>
        </Button>
      </div>
    </div>
  );
}
