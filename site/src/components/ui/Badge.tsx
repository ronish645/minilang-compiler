import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

type Tone = "neutral" | "accent" | "good" | "warning" | "critical";

const TONES: Record<Tone, string> = {
  neutral: "bg-surface-2 text-ink-2 ring-border",
  accent: "bg-accent-soft/60 text-accent-ink ring-accent/25",
  good: "bg-good-mark/10 text-good ring-good-mark/30",
  warning: "bg-warning/15 text-ink ring-warning/40",
  critical: "bg-critical/10 text-critical ring-critical/30",
};

interface BadgeProps {
  children: ReactNode;
  tone?: Tone;
  icon?: ReactNode;
  className?: string;
}

/** A small label. Status tones always come with text (and ideally an icon), never color alone. */
export function Badge({ children, tone = "neutral", icon, className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium ring-1 ring-inset",
        TONES[tone],
        className,
      )}
    >
      {icon}
      {children}
    </span>
  );
}
