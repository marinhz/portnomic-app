# Task 7.4 — Icon spacing and sizing

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

Improve icon legibility and visual comfort by increasing icon sizes and adding adequate spacing between icons that appear next to each other. Address the feedback: "The icons are small and too crowded next to each other."

---

## Problem statement

- **Current state:** Icons use small sizes (`size-3`, `size-3.5`, `size-4`) and tight gaps (`gap-1`, `gap-2`) when grouped together.
- **Pain:** Icons feel cramped and hard to distinguish; action rows and badges look cluttered; reduced usability and visual hierarchy.
- **Goal:** Larger, more legible icons with comfortable spacing that improves scanability and touch targets.

---

## Scope

### 1. Icon size standards

- **Minimum sizes by context:**
  - **Badges (status, labels):** `size-4` (currently `size-3.5` or `size-3`).
  - **Buttons and inline actions:** `size-4` for standard, `size-5` for primary/emphasis.
  - **Page headers and cards:** `size-5` or `size-6` for featured icons.
  - **Sidebar nav:** `size-4` minimum; consider `size-5` when expanded.
- **Audit:** Replace `size-3` and `size-3.5` with `size-4` where icons are primary UI elements (not decorative dots or indicators).

### 2. Spacing between grouped icons

- **Action rows (buttons/links side by side):** Use `gap-3` or `gap-4` instead of `gap-1` or `gap-2`.
- **Badges (icon + label):** Use `gap-1.5` or `gap-2` instead of `gap-1`.
- **Card headers (icon + title):** Use `gap-2` or `gap-3`.
- **Table action columns:** Ensure `gap-2` minimum between icon buttons.

### 3. Priority areas to fix

- **IntegrationsPage:** Status badges (Mail, Inbox, Server icons); Sync/Connect button row.
- **EmailList:** Status badges; header action buttons.
- **Dashboard:** Summary card icons; list item icons; header icon.
- **EmissionsDashboard:** Compliance indicators; action links.
- **AISettingsPage:** Tab icons; card header icons.
- **Sidebar:** Nav item icons; collapse toggle.
- **Data tables:** Any action icon columns (edit, delete, view).

### 4. shadcn Badge default

- **Badge component:** If `[&>svg]:size-3` is set globally, update to `[&>svg]:size-4` for better legibility.
- **Badge gap:** Ensure badges with icon + text use `gap-1.5` or `gap-2`.

---

## Acceptance criteria

- [x] No icons use `size-3` or `size-3.5` for primary UI elements (badges, buttons, nav).
- [x] Grouped action buttons/links use `gap-3` or larger.
- [x] Badges with icons use `gap-1.5` or `gap-2` and icon `size-4`.
- [x] IntegrationsPage, EmailList, and Dashboard icons updated per standards.
- [x] Sidebar nav icons are at least `size-4`.
- [x] Touch targets: icon buttons have adequate padding (min 44×44px for mobile if applicable).

---

## Implementation notes

### Badge with larger icon

```tsx
// Before
<Badge variant={variant} className="gap-1">
  <Icon className="size-3.5 shrink-0" />
  {status}
</Badge>

// After
<Badge variant={variant} className="gap-2">
  <Icon className="size-4 shrink-0" />
  {status}
</Badge>
```

### Action row with more spacing

```tsx
// Before
<div className="flex items-center gap-2">
  <Button><Sync className="size-4" /></Button>
  <Button><Plus className="size-4" /></Button>
</div>

// After
<div className="flex items-center gap-3">
  <Button><Sync className="size-4" /></Button>
  <Button><Plus className="size-4" /></Button>
</div>
```

### Card header icon

```tsx
// Before
<CardTitle className="flex items-center gap-2">
  <Ship className="size-4" />
  Total Vessels
</CardTitle>

// After (for featured cards)
<CardTitle className="flex items-center gap-3">
  <Ship className="size-5 text-maritime-600" />
  Total Vessels
</CardTitle>
```

### Badge component default (if applicable)

```tsx
// In badge.tsx - update SVG size if hardcoded
"[&>svg]:size-4"  // was size-3
```

---

## Related code

- `frontend/src/components/ui/badge.tsx` — default icon size
- `frontend/src/pages/settings/IntegrationsPage.tsx` — badges, action buttons
- `frontend/src/pages/emails/EmailList.tsx` — badges, header actions
- `frontend/src/pages/Dashboard.tsx` — cards, list items
- `frontend/src/layout/Sidebar.tsx` — nav icons
- `frontend/src/pages/emissions/EmissionsDashboard.tsx` — compliance icons
- `frontend/src/pages/settings/AISettingsPage.tsx` — tabs, card headers

---

## Dependencies

- **Task 7.1** (shadcn, Lucide) — icons and components should already be in place. This task refines sizing and spacing only.

---

## Out of scope (for now)

- Changing icon choices (only size and spacing).
- Responsive icon scaling (e.g. different sizes per breakpoint) unless critical.
- New icon components or patterns.
