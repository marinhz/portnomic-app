# Task 13.3 — Port Directory API (List with Search, CRUD)

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Backend** agent with **fastapi-python** skills.

---

## Objective

Ensure Port API supports searchable list and full CRUD. Existing `GET/POST/PUT /ports` may need search query param and pagination enhancements.

---

## Scope

- `GET /ports` — Add `search` query param (name, code, country); pagination.
- `POST /ports` — Create (already exists; ensure coordinates/UN/LOCODE in schema).
- `GET /ports/{id}` — Get single port.
- `PUT /ports/{id}` — Update port.
- Tenant-scoped; RBAC `port_call:read` / `port_call:write` (or port-specific permissions if defined).

---

## Acceptance criteria

- [ ] List supports search by name, code, country.
- [ ] Pagination works; response envelope consistent.
- [ ] Create/update accept new Port schema fields.
