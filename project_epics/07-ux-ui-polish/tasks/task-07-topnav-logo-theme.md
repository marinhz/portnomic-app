# Task 7.7 — Remove logo from topnav and add light/dark theme

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

1. Remove the logo and "Portnomic" badge from the top navigation bar to reduce visual clutter.
2. Add a theme switcher allowing users to choose between light (white) and dark (black) themes, with preference persisted across sessions.

---

## Problem statement

- **Current state:** The topnav displays a logo + "Portnomic" badge alongside user info. The logo is redundant (already in sidebar). The app has no theme options—it uses a fixed light palette.
- **Pain:** Topnav feels crowded; users cannot switch to dark mode for low-light or preference.
- **Goal:** Cleaner topnav (user-focused only); user-selectable light/dark theme with persistence.

---

## Scope

### 1. Remove logo from topnav

- **Location:** `frontend/src/layout/AppLayout.tsx` — header section.
- **Remove:** The entire badge/span containing logo + "Portnomic" text:
  ```tsx
  <span className="flex items-center gap-2.5 rounded-full bg-oxford-blue-50 px-3 py-1 text-xs font-medium text-oxford-blue-700">
    <img src="/Portnomic.svg" alt="" className="h-5 w-5 object-contain" aria-hidden />
    Portnomic
  </span>
  ```
- **Keep:** Sidebar logo and branding unchanged (Task 7.5, 7.3).
- **Result:** Topnav shows only: hamburger (mobile), user avatar, email, Logout. Optionally add theme toggle (see below).

### 2. Add light/dark theme switcher

- **Options:** Light (white) and Dark (black) themes.
- **Placement:** Theme toggle in topnav, right side (e.g. before user avatar or between spacer and user section).
- **Persistence:** Store preference in `localStorage` (e.g. `theme-preference` key: `"light"` | `"dark"`).
- **Default:** Respect `prefers-color-scheme` on first visit if no stored preference; otherwise use stored value.
- **Implementation approach:**
  - Add `class="dark"` to `<html>` when dark theme is active (Tailwind dark mode).
  - Use CSS variables or Tailwind `dark:` variants for theme-aware styles.
  - Theme toggle: Sun/Moon icon or dropdown (Light / Dark).

### 3. Theme-aware styling

- **Current:** App uses `bg-white`, `bg-slate-50`, `border-slate-200`, `text-slate-600`, etc.
- **Required:** Add `dark:` variants for:
  - Header: `dark:bg-slate-900 dark:border-slate-700`
  - Main: `dark:bg-slate-950 dark:text-slate-100`
  - Sidebar: `dark:bg-slate-900 dark:border-slate-700`
  - Cards, inputs, buttons: appropriate `dark:` overrides
- **Scope:** Focus on layout (AppLayout, Sidebar) and key pages (Dashboard, common components). Full dark-mode audit can be a follow-up.

---

## Acceptance criteria

### Logo removal

- [ ] Logo and "Portnomic" badge removed from topnav.
- [ ] Topnav shows only: hamburger (mobile), user avatar, email, Logout (and theme toggle).
- [ ] No layout regression; spacing and alignment remain correct.

### Theme switcher

- [ ] Theme toggle visible in topnav (Sun/Moon icon or dropdown).
- [ ] Clicking toggle switches between light and dark.
- [ ] Preference persisted in `localStorage`; survives page reload.
- [ ] First visit: use `prefers-color-scheme: dark` if no stored preference.
- [ ] `<html>` has `class="dark"` when dark theme is active.

### Theme styling

- [ ] Header, sidebar, and main content area have dark-mode styles.
- [ ] Text remains readable; contrast meets WCAG AA where applicable.
- [ ] No flash of wrong theme on load (apply theme before paint if possible).

---

## Implementation notes

### Theme provider / hook

```tsx
// Example: useTheme hook
const THEME_KEY = "theme-preference";
type Theme = "light" | "dark";

function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_KEY) as Theme | null;
    if (stored) return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  const toggle = () => setTheme((t) => (t === "light" ? "dark" : "light"));
  return { theme, setTheme, toggle };
}
```

### Tailwind dark mode

- Ensure `tailwind.config` has `darkMode: "class"` (or `"selector"`).
- Add `dark:` variants to layout and components.

### Theme toggle button

```tsx
// In AppLayout header
<button
  onClick={toggleTheme}
  className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
  aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
>
  {theme === "dark" ? <Sun className="size-5" /> : <Moon className="size-5" />}
</button>
```

---

## Related code

- `frontend/src/layout/AppLayout.tsx` — topnav, logo removal, theme toggle placement
- `frontend/src/layout/Sidebar.tsx` — dark-mode styles for sidebar
- `frontend/tailwind.config.*` — dark mode config
- `frontend/index.html` — ensure no inline theme that could cause flash

---

## Dependencies

- **Task 7.1** (shadcn, Lucide) — Sun/Moon icons available.
- **Task 7.3** (Portnomic rebrand) — sidebar logo remains; only topnav logo removed.

---

## Out of scope (for now)

- System theme sync (auto-update when OS theme changes) — optional enhancement.
- Per-page or per-route theme overrides.
- Full dark-mode audit of every page (focus on layout + key flows first).
