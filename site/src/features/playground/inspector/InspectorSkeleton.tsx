import { Loader2 } from "lucide-react";
import { Skeleton } from "../../../components/ui/StateViews";

/** Shown while Pyodide downloads (~10 MB the first time, cached after). */
export function InspectorSkeleton({ progress }: { progress: string }) {
  return (
    <div role="status" aria-live="polite" className="space-y-4">
      <div className="flex items-center gap-2 text-sm text-ink-2">
        <Loader2 className="size-4 animate-spin text-accent" aria-hidden />
        <span>{progress}</span>
      </div>
      <p className="text-xs text-muted">
        The first visit downloads a Python runtime (about 10 MB). After that it's cached. The
        editor already works, so start typing.
      </p>
      <div className="space-y-2 rounded-xl border border-border bg-surface p-3">
        <Skeleton className="h-3 w-2/3" />
        <Skeleton className="h-3 w-1/2" />
        <Skeleton className="h-3 w-3/4" />
        <Skeleton className="h-3 w-1/3" />
      </div>
      <Skeleton className="h-20 w-full" />
    </div>
  );
}
