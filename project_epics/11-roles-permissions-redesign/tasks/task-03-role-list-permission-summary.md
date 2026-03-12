# Task 11.3 — RoleList: Permission Summary by Module

**Epic:** [11-roles-permissions-redesign](../epic.md)

---

## Objective

Improve the RoleList so each role shows a module-based permission summary (e.g. "Vessels ✓, DA ✓, Admin ✗") instead of a long list of raw permission tags. Makes it easier to scan and compare roles.

---

## Problem statement

- **Current:** RoleList shows permissions as individual tags (`vessel:read`, `vessel:write`, `da:read`, …) — hard to scan.
- **Goal:** Summarize by module: "Vessels ✓, Port calls ✓, DA ✓, AI ✓, Admin ✗" — quick visual understanding.

---

## Scope

### Frontend

- **Permission summary column:** Replace or supplement the raw permissions column with a module summary.
- **Format options:**
  - Badges: "Vessels", "Port calls", "DA", "AI" (only modules where role has at least one permission)
  - Checkmarks: "Vessels ✓, Port calls ✓, DA ✓, Admin ✗"
  - Expandable: Summary by default; click to expand full permission list
- **Module mapping:** Reuse same module groups as Task 11.2 (Vessels, Port calls, DA, AI, Admin, Billing, Settings).
- **Tooltip/detail:** Hover or expand to see exact permissions if needed.

---

## Acceptance criteria

- [ ] Role list shows a module-based summary for each role.
- [ ] Admins can quickly see which modules a role has access to.
- [ ] Full permission list still accessible (expand, tooltip, or detail view).

---

## Related code

- `frontend/src/pages/admin/RoleList.tsx` — Current implementation with permission tags
- Task 11.2 — Shared module/permission metadata
