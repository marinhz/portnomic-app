# Task 14.9 — Port Call Dashboard Integration

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

Integrate SentinelAlert and SideBySideAudit into the Port Call dashboard so users see Sentinel findings in context with port call details, DAs, and other operational data.

---

## Scope

### 1. Dashboard placement

- **SentinelAlert:** Place at top of Port Call detail page or in a dedicated "Alerts" section when discrepancies exist.
- **SideBySideAudit:** Accessible via SentinelAlert "View details" or a dedicated "Sentinel Audit" tab/section on the Port Call page.
- **Empty state:** When no discrepancies, optionally show "No Sentinel alerts" or omit section.

### 2. Routing & data loading

- Port Call detail route loads discrepancies (or include in port call loader).
- React Router v7: use loaders for data; consider parallel loading of port call + discrepancies.
- Cache/invalidation: re-fetch when new document parsed or on manual refresh.

### 3. UX flow

- User lands on Port Call → sees SentinelAlert if discrepancies exist.
- User clicks through → SideBySideAudit in modal, drawer, or inline section.
- Clear navigation back to port call overview.

### 4. Permissions (optional)

- Align with RBAC: only users with `port_call:read` (or Sentinel-specific permission) see Sentinel section.
- Feature gate: hide for Starter plan if Sentinel is premium.

---

## Acceptance criteria

- [ ] SentinelAlert visible on Port Call detail when discrepancies exist.
- [ ] SideBySideAudit accessible from alert or tab.
- [ ] Data loaded via route loader or equivalent.
- [ ] Empty state handled; no layout shift when no alerts.
- [ ] Navigation and back flow clear.

---

## Related code

- Port Call detail page / route
- `frontend/src/routes/` — React Router setup
- Epic 13 — Manual port/port call management
- Epic 8 — Feature gating (if applicable)

---

## Dependencies

- Task 14.7 — SentinelAlert
- Task 14.8 — SideBySideAudit
- Epic 3 — Port Call detail UI
- Backend: GET /api/port-calls/{id}/discrepancies
