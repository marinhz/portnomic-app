# Task 3.5 — POST /da/generate and GET /da/{id} API

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Generate Proforma or Final DA for a port call via API; get DA by id with RBAC (EDD §7.2).

## Scope

- **POST /da/generate** — Body: port_call_id, type (proforma|final). Run formula engine; create DA in draft; return DA payload (id, port_call_id, type, status, line_items, totals).
- **GET /da/{id}** — Return DA; JWT, da:read; tenant-scoped (404 if wrong tenant).
- Permissions: da:write for generate, da:read for get.

## Acceptance criteria

- [ ] Generate creates DA in draft with correct line items and totals; port_call must belong to tenant.
- [ ] Get returns full DA; 403/404 for unauthorized or missing DA.
- [ ] Response shape matches OpenAPI and frontend expectations.
