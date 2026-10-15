import { cn } from "../../lib/cn";
import { modelColor, modelShort } from "../../lib/models";

interface ModelChipProps {
  model: string;
  label?: string;
  className?: string;
}

/** A model's color dot plus its name: identity is never carried by color alone. */
export function ModelChip({ model, label, className }: ModelChipProps) {
  return (
    <span className={cn("inline-flex items-center gap-2 text-sm text-ink", className)}>
      <span
        aria-hidden
        className="size-2.5 shrink-0 rounded-full"
        style={{ backgroundColor: modelColor(model) }}
      />
      {label ?? modelShort(model)}
    </span>
  );
}
