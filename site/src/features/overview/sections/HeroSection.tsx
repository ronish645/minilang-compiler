import { ArrowRight, BarChart3 } from "lucide-react";
import { Link } from "react-router-dom";
import { Container } from "../../../components/layout/Page";
import { buttonClasses } from "../../../components/ui/Button";
import { GitHubIcon } from "../../../components/ui/GitHubIcon";
import { cn } from "../../../lib/cn";
import { REPO_URL } from "../../../lib/links";
import { HeroCodeCard } from "./HeroCodeCard";

export function HeroSection() {
  return (
    <section aria-labelledby="hero-title" className="relative isolate overflow-hidden border-b border-border">
      <div
        aria-hidden
        className="bg-dots absolute inset-0 -z-10 [mask-image:radial-gradient(ellipse_80%_70%_at_50%_0%,black,transparent)]"
      />
      <Container className="grid items-center gap-12 py-14 sm:py-20 lg:grid-cols-[1.05fr_1fr] lg:gap-16 lg:py-24">
        <div className="min-w-0">
          <p className="inline-flex items-center gap-2 rounded-full border border-border bg-surface/80 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-accent backdrop-blur">
            Compiler · LLM evaluation
          </p>
          <h1
            id="hero-title"
            className="mt-5 text-4xl font-semibold leading-[1.08] tracking-tight text-ink text-balance sm:text-5xl lg:text-[3.5rem]"
          >
            Can an LLM learn a programming language it has never seen?
          </h1>
          <p className="mt-5 max-w-xl text-lg text-ink-2 text-pretty">
            MiniLang was created for this question, so it can't be in any model's training data. The
            project is a from-scratch compiler for it, plus a benchmark where Claude, GPT and a local
            model learn it from the spec alone.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/playground" className={buttonClasses("primary")}>
              Try the playground
              <ArrowRight className="size-4" aria-hidden />
            </Link>
            <Link to="/benchmark" className={buttonClasses("secondary")}>
              <BarChart3 className="size-4" aria-hidden />
              See the results
            </Link>
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              className={cn(buttonClasses("ghost"), "text-ink-2")}
            >
              <GitHubIcon className="size-4" />
              Source on GitHub
            </a>
          </div>
        </div>
        <div className="min-w-0">
          <HeroCodeCard />
        </div>
      </Container>
    </section>
  );
}
