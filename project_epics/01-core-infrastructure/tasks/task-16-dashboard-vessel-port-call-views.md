# Task 1.16 — Dashboard and vessel/port call views

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Dashboard with placeholder or minimal data; vessel and port call list/detail/CRUD views using the API (EDD §4.1).

## Scope

- **Dashboard:** Placeholder or minimal KPIs; links to vessels, port calls (data tables ready for later epics).
- **Vessels:** List (table), create form, edit form, detail view; call GET/POST/PUT /vessels.
- **Port calls:** List with filters (e.g. vessel_id, status), create/edit/detail; call GET/POST/PUT /port-calls.
- RBAC-driven visibility: show only what user has permission for.

## Acceptance criteria

- [ ] User can list, create, update, and view vessels and port calls within their tenant.
- [ ] List views support pagination and (where applicable) filters; forms validate and show API errors.
- [ ] No cross-tenant data visible; tenant context is implicit from auth.
