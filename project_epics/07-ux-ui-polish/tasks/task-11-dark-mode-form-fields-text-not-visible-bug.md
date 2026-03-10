# Task 7.11 — Bug: Dark mode — form fields text not visible (port call and other forms)

**Epic:** [07-ux-ui-polish](../epic.md)

**Type:** Bug

---

## Objective

Fix dark mode so that form field text (typed and placeholder) is clearly visible across all forms, starting with the create/edit port call form and auditing other forms for the same issue.

---

## Problem statement

- **User report:** When creating a new port call in dark mode, form fields text is not visible.
- **Expected:** All form inputs (text, selects, date inputs) have readable text and placeholders in both light and dark themes.
- **Actual:** In dark mode, input text and labels may be invisible or have poor contrast due to hardcoded light-theme colors (e.g. `text-slate-700`, `bg-white`, `border-slate-300` without dark variants).

---

## Scenario

1. User switches to dark mode (via theme toggle in topnav).
2. User navigates to create a new port call (`/port-calls/new`).
3. **Observed:** Form fields (Vessel, Port, ETA, ETD, Status) show text that is not visible or has insufficient contrast.
4. **Observed:** Labels, placeholders, and typed text may blend into the background or be unreadable.

---

## Scope

### 1. Port Call form (primary)

- **Location:** `frontend/src/pages/port-calls/PortCallForm.tsx`
- **Issues to fix:**
  - `inputClass` — add dark-mode text and background (e.g. `text-slate-900 dark:text-slate-100`, `bg-white dark:bg-slate-800`, `border-slate-300 dark:border-slate-600`)
  - Page title — `text-slate-800` → add `dark:text-slate-100`
  - Card container — `bg-white border-slate-200` → add `dark:bg-slate-800 dark:border-slate-700`
  - Labels — `text-slate-700` → add `dark:text-slate-300`
  - Error banner — ensure readable in dark mode (`dark:bg-red-900/30 dark:text-red-200` or similar)
  - Cancel button — `text-slate-700 border-slate-300 hover:bg-slate-50` → add dark variants

### 2. Audit and fix other forms

Check and fix dark mode visibility for:

- `frontend/src/pages/vessels/VesselForm.tsx`
- `frontend/src/pages/da/DAGenerate.tsx`
- `frontend/src/pages/admin/UserForm.tsx`
- `frontend/src/pages/admin/RoleForm.tsx`
- `frontend/src/pages/platform/CompanyForm.tsx`
- `frontend/src/pages/settings/ProfilePage.tsx`
- `frontend/src/pages/settings/AISettingsPage.tsx`
- `frontend/src/pages/settings/IntegrationsPage.tsx`
- `frontend/src/pages/settings/Billing.tsx`
- `frontend/src/auth/LoginPage.tsx` (already addressed in Task 7.9; verify no regression)

### 3. Shared input components

- **Location:** `frontend/src/components/ui/input.tsx` (shadcn Input)
- Ensure Input, Select, Textarea components use theme-aware colors if used by forms.
- If forms use raw HTML `<input>`/`<select>` with custom classes, apply consistent dark-mode classes.

---

## Acceptance criteria

- [ ] Create/edit port call form: all field text (labels, placeholders, typed values) is clearly visible in dark mode.
- [ ] Port call form: card container, error banner, and buttons have appropriate dark-mode styling.
- [ ] All audited forms (Vessel, DA Generate, User, Role, Company, Profile, AI Settings, Integrations, Billing) have visible form text in dark mode.
- [ ] No regression in light mode appearance.
- [ ] Sufficient contrast (WCAG AA) for text in both themes.

---

## Implementation notes

### Pattern for dark-mode form fields

```tsx
// Input/select with theme-aware styling
const inputClass =
  "w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-500 dark:placeholder:text-slate-400 transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20";

// Labels
className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"

// Card container
className="... bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 ..."
```

### Consider shadcn Input

If forms use raw HTML inputs, consider migrating to shadcn `Input` and `Select` components which may already have dark-mode support via CSS variables.

---

## Related code

- `frontend/src/pages/port-calls/PortCallForm.tsx` — primary fix
- `frontend/src/components/ui/input.tsx` — shadcn Input (theme variables)
- `frontend/src/hooks/useTheme.ts` — theme context
- Other form pages listed in Scope §2

---

## Dependencies

- Task 7.1 — shadcn components
- Task 7.7 — theme toggle (dark mode must be functional)
- Task 7.9 — login page input visibility (related; verify no overlap/regression)
