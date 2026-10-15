import { Check, Link as LinkIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { Button } from "../../../components/ui/Button";

const RESET_MS = 1800;

/** Copies the current URL, which already names the filters and the open episode. */
export function CopyLinkButton() {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => {
    if (state === "idle") return;
    const timer = window.setTimeout(() => setState("idle"), RESET_MS);
    return () => window.clearTimeout(timer);
  }, [state]);

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      setState("copied");
    } catch {
      setState("failed");
    }
  };

  const label = state === "copied" ? "Copied" : state === "failed" ? "Copy failed" : "Copy link";
  return (
    <Button
      size="sm"
      variant="secondary"
      onClick={copy}
      icon={state === "copied" ? <Check className="size-3.5 text-good" aria-hidden /> : <LinkIcon className="size-3.5" aria-hidden />}
    >
      <span aria-live="polite">{label}</span>
    </Button>
  );
}
