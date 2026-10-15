import { CircleSlash } from "lucide-react";

/** Shown in a tab whose stage didn't run. */
export function EmptyStage({ message }: { message: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 px-6 py-16 text-center">
      <span className="grid size-10 place-items-center rounded-full bg-surface-2 text-muted">
        <CircleSlash className="size-5" aria-hidden />
      </span>
      <p className="max-w-xs text-sm text-ink-2">{message}</p>
    </div>
  );
}
