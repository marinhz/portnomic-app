# Task 7.5 — Sidebar collapse: keep icon position, hide text only

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

When the sidebar is collapsed, icons should remain in the **exact same position** as when expanded. Only the text labels should disappear—no icon shifting, centering, or layout jump.

---

## Problem statement

- **Current state:** When the sidebar collapses, nav items may use `justify-center` or different padding, causing icons to shift (e.g. toward center). Header and user section also center content when collapsed.
- **Pain:** Visual jump when toggling collapse; icons feel misaligned; inconsistent muscle memory for users who rely on icon position.
- **Goal:** Icons stay fixed in place; collapse = text fades away, icons remain aligned as in expanded state.

---

## Scope

### 1. Nav items (NavItem)

- **Expanded:** Icon + text, left-aligned with `px-2.5` (or equivalent).
- **Collapsed:** Same left padding, same icon position; only the text (`<span>{label}</span>`) is hidden.
- **Do not:** Center the nav item (`justify-center`), change padding, or shift icon alignment when collapsed.
- **Keep:** Tooltip on hover for collapsed state (label shown on hover).

### 2. Header (logo + collapse toggle)

- **Expanded:** Logo + "Portnomic" text + collapse button, left-aligned.
- **Collapsed:** Logo and collapse button stay in the **same horizontal position** as when expanded; only the "Portnomic" text is hidden.
- **Do not:** Center the header content when collapsed.

### 3. User section (footer)

- **Expanded:** Avatar + email, left-aligned.
- **Collapsed:** Avatar stays in the **same position** as when expanded; only the email text is hidden.
- **Do not:** Center the avatar when collapsed.

---

## Acceptance criteria

- [ ] Nav item icons keep the same left offset when sidebar is collapsed vs expanded.
- [ ] Header logo and collapse button keep the same left offset when collapsed.
- [ ] User avatar keeps the same left offset when collapsed.
- [ ] Only text (labels, "Portnomic", email) is hidden when collapsed—no layout shift.
- [ ] Tooltips still work for collapsed nav items.
- [ ] Collapse/expand transition feels smooth with no icon position jump.

---

## Implementation notes

### NavItem — same padding, no centering

```tsx
// Current (problematic): collapsed may center or change layout
function navLinkClass({ isActive }: { isActive: boolean }, collapsed?: boolean) {
  return `flex items-center gap-2.5 rounded-md px-2.5 py-2.5 ... ${
    collapsed ? "justify-start py-3.5" : ""  // avoid justify-center
  }`;
}

// NavItem: same padding for both states
<NavLink className={(opts) => navLinkClass(opts, isCollapsed)}>
  <Icon className="size-4 shrink-0" />  {/* same size expanded/collapsed */}
  {!isCollapsed && <span>{label}</span>}
</NavLink>
```

- Use **identical** `px-2.5` (or `px-3`) for both expanded and collapsed.
- Use **identical** icon size (`size-4`) for both states.
- Do **not** add `justify-center` when collapsed—keep `justify-start` (or equivalent) so icons stay left-aligned.

### Header — same layout, hide text only

```tsx
// Keep same flex layout; only hide the text span
<div className={`flex h-12 shrink-0 items-center gap-2 px-3 ...`}>
  <div className="flex shrink-0 items-center gap-2 min-w-0">
    <img src="/Portnomic.svg" ... />
    {!isCollapsed && <span>Portnomic</span>}
  </div>
  <button ...>...</button>
</div>
```

- Use the **same** `px-3` and `gap-2` for both states.
- Do **not** switch to `justify-center px-0` when collapsed.

### User section — same layout, hide text only

```tsx
// Keep same padding; only hide the email
<div className={`flex shrink-0 items-center gap-2 border-t ... p-1.5`}>
  <div className="h-6 w-6 ...">...</div>
  {!isCollapsed && <p>...</p>}
</div>
```

- Use the **same** `p-1.5` and `gap-2` for both states.
- Do **not** add `justify-center` when collapsed.

---

## Related code

- `frontend/src/layout/Sidebar.tsx` — `navLinkClass`, `NavItem`, header, user section

---

## Dependencies

- **Task 7.1** (shadcn, Lucide) — icons and Tooltip in place.
- **Task 7.3** (Portnomic rebrand) — logo and styling.

---

## Out of scope (for now)

- Changing sidebar width values.
- Adding animation for collapse/expand (unless trivial).
- Mobile drawer behavior (focus on desktop collapse).
