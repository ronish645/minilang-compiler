import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

const current = (): Theme =>
  document.documentElement.dataset.theme === "dark" ? "dark" : "light";

/** The active theme, plus a toggle that remembers the choice. */
export function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(current);

  useEffect(() => {
    // Follow OS changes until the visitor picks a theme themselves.
    const media = matchMedia("(prefers-color-scheme: dark)");
    const onChange = (event: MediaQueryListEvent) => {
      let saved: string | null = null;
      try {
        saved = localStorage.getItem("theme");
      } catch {
        /* storage unavailable: just follow the OS */
      }
      if (saved) return;
      const next: Theme = event.matches ? "dark" : "light";
      document.documentElement.dataset.theme = next;
      setTheme(next);
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, []);

  const toggle = useCallback(() => {
    const next: Theme = current() === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      localStorage.setItem("theme", next);
    } catch {
      /* the choice just won't persist */
    }
    setTheme(next);
  }, []);

  return [theme, toggle];
}
