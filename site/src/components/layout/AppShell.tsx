import { Menu, Moon, Sun, X } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../lib/cn";
import { GitHubIcon } from "../ui/GitHubIcon";
import { REPO_URL } from "../../lib/links";
import { useTheme } from "../../lib/theme";

const NAV = [
  { to: "/", label: "Overview" },
  { to: "/playground", label: "Playground" },
  { to: "/benchmark", label: "Benchmark" },
  { to: "/explorer", label: "Episodes" },
];

function Logo() {
  return (
    <NavLink to="/" className="flex items-center gap-2.5 font-semibold tracking-tight text-ink">
      <span className="grid size-8 place-items-center rounded-lg bg-accent text-white shadow-sm">
        <svg viewBox="0 0 32 32" className="size-5" aria-hidden>
          <path
            d="M8 23V9l8 8 8-8v14"
            fill="none"
            stroke="currentColor"
            strokeWidth="3.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span>
        MiniLang
        <span className="ml-1.5 hidden font-normal text-ink-2 sm:inline">compiler &amp; LLM benchmark</span>
      </span>
    </NavLink>
  );
}

function ThemeToggle() {
  const [theme, toggle] = useTheme();
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={`Switch to ${next} theme`}
      className="grid size-9 place-items-center rounded-lg text-ink-2 transition hover:bg-surface-2 hover:text-ink"
    >
      {theme === "dark" ? <Sun className="size-4" /> : <Moon className="size-4" />}
    </button>
  );
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "rounded-lg px-3 py-1.5 text-sm font-medium transition",
    isActive ? "bg-surface-2 text-ink" : "text-ink-2 hover:text-ink",
  );

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    setMenuOpen(false);
    window.scrollTo({ top: 0 });
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen flex-col">
      {/* A button, not href="#main": under HashRouter a #fragment would be read as a route. */}
      <button
        type="button"
        onClick={() => document.getElementById("main")?.focus()}
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2"
      >
        Skip to content
      </button>
      <header className="sticky top-0 z-40 border-b border-border bg-page/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6">
          <Logo />
          <nav aria-label="Main" className="hidden items-center gap-1 md:flex">
            {NAV.map((item) => (
              <NavLink key={item.to} to={item.to} end={item.to === "/"} className={navClass}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="flex items-center gap-1">
            <a
              href={REPO_URL}
              target="_blank"
              rel="noreferrer"
              aria-label="Source code on GitHub"
              className="grid size-9 place-items-center rounded-lg text-ink-2 transition hover:bg-surface-2 hover:text-ink"
            >
              <GitHubIcon className="size-4" />
            </a>
            <ThemeToggle />
            <button
              type="button"
              className="grid size-9 place-items-center rounded-lg text-ink-2 hover:bg-surface-2 md:hidden"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              {menuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
            </button>
          </div>
        </div>
        {menuOpen && (
          <nav aria-label="Main" className="border-t border-border px-4 py-3 md:hidden">
            <div className="flex flex-col gap-1">
              {NAV.map((item) => (
                <NavLink key={item.to} to={item.to} end={item.to === "/"} className={navClass}>
                  {item.label}
                </NavLink>
              ))}
            </div>
          </nav>
        )}
      </header>

      <main id="main" tabIndex={-1} className="flex-1 focus:outline-none">
        {children}
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-8 text-sm text-ink-2 sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>
            Built by Ronish Shrestha · compiler, benchmark and site are{" "}
            <a href={REPO_URL} className="font-medium text-ink underline-offset-4 hover:underline">
              open source
            </a>
          </p>
          <p className="text-muted">Python · React · Pyodide · Tailwind</p>
        </div>
      </footer>
    </div>
  );
}
