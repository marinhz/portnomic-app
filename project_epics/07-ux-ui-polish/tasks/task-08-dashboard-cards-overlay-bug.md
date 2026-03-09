# Task 7.8 — Bug: Dashboard cards overlay — vessels and portcalls records go over disbursements cards

**Epic:** [07-ux-ui-polish](../epic.md)

**Type:** Bug

---

## Objective

Fix the bug where cards on the Dashboard overlap incorrectly: vessels and portcalls records visually overlay or extend over the disbursements (DAs) cards, causing layout and readability issues.

---

## Problem statement

- **User report:** Cards on the dashboard are overlayed; vessels and portcalls records go over disbursements cards.
- **Expected:** All dashboard sections (summary cards, Recent Vessels, Recent Port Calls, Recent DAs) render in a clear, non-overlapping layout with proper stacking and spacing.
- **Actual:** Vessels and/or portcalls record sections overlap the disbursements cards, obscuring content or creating a confusing visual hierarchy.

---

## Scenario

1. User navigates to the Dashboard (`/` or `/dashboard`).
2. Dashboard loads with summary cards (Total Vessels, Port Calls, Active Port Calls, DAs) and recent lists (Vessels, Port Calls, Disbursements).
3. **Observed:** The vessels and portcalls record sections overlap or extend over the disbursements cards, causing:
   - Content from one section appearing on top of another
   - Disbursements cards partially or fully hidden
   - Broken or inconsistent layout depending on viewport size

---

## Scope

- **Root cause analysis:** Identify why vessels/portcalls sections overlap disbursements cards.
- **Possible causes:**
  - CSS `z-index` or stacking context issues (e.g. absolute/fixed positioning, transforms).
  - Grid or flex layout overflow (content overflowing into adjacent areas).
  - Responsive breakpoints causing incorrect column/row placement.
  - Missing or incorrect `overflow` handling on list containers.
  - Height/position conflicts between sibling sections.
- **Fix:** Ensure each dashboard section has correct layout, stacking, and overflow behavior so no overlap occurs.
- **Verification:** All sections render without overlap at common viewport sizes (mobile, tablet, desktop).

---

## Root cause (resolved)

- **Flexbox min-height overflow:** In a flex column layout, children default to `min-height: auto`, which prevents them from shrinking below their content size. This caused overflow from the Vessels/Port Calls grid to spill into the DAs card area.
- **Grid stretch behavior:** The grid used default `align-items: stretch`, which could cause height conflicts when cards had different content heights.
- **Layout structure:** Using nested flex + grid allowed implicit placement and potential overlap. The DAs card was a sibling in a flex container, which could lead to stacking/overflow issues.

**Fix applied (v2):**
1. **Single grid with explicit placement:** Replaced nested flex+grid with one grid using `lg:grid-rows-[auto_auto]`, `lg:row-start-1 lg:col-start-1/2` for Vessels/Port Calls, and `lg:col-span-2 lg:row-start-2` for DAs — ensures DAs is always in row 2, never overlapping.
2. **CardContent overflow:** Added `min-h-0 overflow-hidden` to CardContent for list cards so flex children can shrink and contain overflow.
3. **min-h-0 on cards:** Cards with scrollable content get `min-h-0` for proper flex containment.

---

## Acceptance criteria

- [x] Root cause documented.
- [x] Vessels and portcalls records no longer overlap disbursements cards.
- [x] All dashboard sections (summary cards, Recent Vessels, Recent Port Calls, Recent DAs) display in correct visual order without overlay.
- [x] Layout remains correct at mobile, tablet, and desktop viewport sizes.
- [x] No regression in existing dashboard functionality or styling.

---

## Related code

- `frontend/src/pages/Dashboard.tsx` — main dashboard layout, grid structure, card sections
- `frontend/src/components/ui/card.tsx` — Card component styling
- Dashboard layout structure: summary grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-4`), recent lists grid

---

## Dependencies

- Task 7.2 (Dashboard UX with shadcn) — dashboard layout and card structure.
