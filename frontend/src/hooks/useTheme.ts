import { useState, useEffect } from "react";

const THEME_KEY = "theme-preference";
export type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const stored = localStorage.getItem(THEME_KEY) as Theme | null;
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const setTheme = (value: Theme) => setThemeState(value);
  const toggle = () =>
    setThemeState((t) => (t === "light" ? "dark" : "light"));

  return { theme, setTheme, toggle } as const;
}
