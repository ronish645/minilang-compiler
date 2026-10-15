import { SEQ_STEPS } from "../lib/sequential";

/** A stepped sequential legend: what each shade of the ramp means. */
export function ScaleLegend({ label }: { label: string }) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-2 text-xs text-ink-2">
      <span>{label}</span>
      <ul aria-label={`${label} color scale`} className="flex gap-0.5">
        {SEQ_STEPS.map((step) => (
          <li key={step.label} className="flex flex-col items-center gap-1">
            <span aria-hidden className="h-2.5 w-12 rounded-[3px] sm:w-14" style={{ background: step.token }} />
            <span className="tabular-nums text-muted">{step.label}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
