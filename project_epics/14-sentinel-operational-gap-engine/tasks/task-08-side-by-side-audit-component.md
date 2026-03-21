# Task 14.8 — SideBySideAudit Component

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev** and **tailwind-design-system** skills.

---

## Objective

Create the `SideBySideAudit` table component showing Vendor Claims vs. Operational Reality vs. Variance. This enables users to quickly identify and investigate discrepancies.

---

## Scope

### 1. SideBySideAudit component

- **Props:** `discrepancies: Discrepancy[]`, `portCallId: string`.
- **Layout:** Table (or card-based) with three columns:
  - **Column 1: "Vendor Claims"** — Values from Invoice/DA (e.g. invoiced hours, berth days).
  - **Column 2: "Operational Reality"** — Values from SOF, AIS, Noon Report.
  - **Column 3: "Variance"** — Difference; highlighted in red when significant.
- **Row source:** Each discrepancy maps to a row; use `raw_evidence` for vendor vs operational values if available.

### 2. Data mapping

- Backend `DiscrepancyResponse` should include `raw_evidence` or structured fields for vendor value, operational value, variance.
- Frontend renders these in the three columns; variance column uses conditional red styling.

### 3. Design

- Table: accessible, responsive (horizontal scroll on small screens if needed).
- Red highlight for variance column when severity is High or value exceeds threshold.
- Optional: expandable row for full description and source document links.

---

## Acceptance criteria

- [ ] SideBySideAudit renders three-column layout.
- [ ] Vendor Claims, Operational Reality, Variance displayed per discrepancy.
- [ ] Variance highlighted in red for high-risk items.
- [ ] Optional: expand for description and source documents.
- [ ] Accessible table semantics.

---

## Related code

- `frontend/src/components/sentinel/SideBySideAudit.tsx`
- Epic 12 — Discrepancy UI (DA workspace) for reference pattern
- Task 14.7 — SentinelAlert links to this view

---

## Dependencies

- Task 14.3 — DiscrepancyResponse schema, raw_evidence structure
- Task 14.7 — Integration point from SentinelAlert
