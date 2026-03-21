# Task 14.7 — SentinelAlert Component

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev** and **tailwind-design-system** skills.

---

## Objective

Create a high-visibility `SentinelAlert` card component that surfaces Sentinel discrepancies in the Port Call dashboard. Alerts should draw attention to financial and operational risks without overwhelming the UI.

---

## Scope

### 1. SentinelAlert component

- **Props:** `discrepancies: Discrepancy[]`, `portCallId: string`, optional `onDismiss` or `onViewDetails`.
- **Layout:** Card with severity-based styling (e.g. red accent for High, amber for Medium).
- **Content:**
  - Count of discrepancies by severity.
  - Summary: "X high-risk, Y potential errors" or similar.
  - Link or button to open SideBySideAudit view.
- **Visibility:** Only render when `discrepancies.length > 0`.

### 2. Design

- Use Tailwind; align with existing design system (shadcn if present).
- High visibility: consider icon (e.g. shield-alert, alert-triangle), clear typography.
- Accessible: ARIA labels, keyboard navigation.

### 3. API integration

- Fetch discrepancies for port call via `GET /api/port-calls/{id}/discrepancies` or equivalent.
- Handle loading and error states.

---

## Acceptance criteria

- [ ] SentinelAlert renders when discrepancies exist for the port call.
- [ ] Severity-based visual styling applied.
- [ ] Summary shows count by severity; link to audit view.
- [ ] Loading and error states handled.
- [ ] Accessible and responsive.

---

## Related code

- `frontend/src/components/sentinel/` or equivalent
- Port Call detail page / dashboard
- Epic 14 — API endpoint for discrepancies (backend task)

---

## Dependencies

- Task 14.3 — discrepancies API
- Epic 3 — Port Call detail UI
- tailwind-design-system skill
