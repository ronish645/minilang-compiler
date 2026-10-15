import type { ReactNode } from "react";
import { SectionHeading } from "../../../components/ui/SectionHeading";
import type { SectionId } from "../lib/sections";

interface BenchmarkSectionProps {
  id: SectionId;
  eyebrow: string;
  title: string;
  takeaway: ReactNode;
  children: ReactNode;
}

/** One analysis section: a question, a computed takeaway, then the evidence. */
export function BenchmarkSection({ id, eyebrow, title, takeaway, children }: BenchmarkSectionProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-32 lg:scroll-mt-24">
      <SectionHeading id={`${id}-title`} eyebrow={eyebrow} title={title} description={takeaway} />
      <div className="mt-6">{children}</div>
    </section>
  );
}
