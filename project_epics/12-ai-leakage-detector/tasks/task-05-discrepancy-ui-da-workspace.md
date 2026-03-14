# Task 12.5 — Discrepancy UI (DA Workspace)

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

Add a side-by-side view in the DA Workspace showing "Invoiced Value" vs. "System Expected Value" for line items. Visual flags on line items that failed the audit logic.

---

## Scope

### 1. API

- `GET /da/{id}/anomalies` — List anomalies for a DA (JWT, da:read).
- Response includes rule_id, severity, line_item_ref, invoiced_value, expected_value, description.

### 2. DA Workspace UI

- **Side-by-side view:** For each line item with anomalies, show:
  - Invoiced value (from DA line item)
  - System expected value (from anomaly record)
  - Rule that failed (LD-001, LD-002, etc.)
- **Visual flags:** Badge or icon on line items that failed audit (e.g. warning icon, color-coded by severity).
- **Expandable detail:** Click to see full anomaly description and evidence.

### 3. Design

- Use shadcn/ui components (Table, Badge, Alert, etc.).
- Responsive; fits within existing DA workspace layout.

---

## Acceptance criteria

- [ ] API returns anomalies for a DA; frontend fetches and displays.
- [ ] Side-by-side view shows invoiced vs. expected value for flagged line items.
- [ ] Visual flags (badge/icon) on failed line items; severity-appropriate styling.
- [ ] Expandable detail for full anomaly description.

---

## Related code

- `frontend/` — DA workspace routes and components
- `backend/app/api/` — DA anomalies endpoint
- shadcn/ui — Table, Badge, Alert

---

## Dependencies

- Task 12.1 — Anomaly table
- Epic 3 — DA workspace, DA entity
