# Task 1.9 — Port call service and API

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

CRUD for port calls, linked to vessel and port; tenant-scoped (EDD §4.2, §7.2).

## Scope

- **GET /port-calls** — List port calls (filters: vessel_id, status, etc.), tenant-scoped.
- **POST /port-calls** — Create port call (JWT, port_call:write).
- **GET /port-calls/{id}** — Get port call (JWT, port_call:read).
- **PUT /port-calls/{id}** — Update port call (JWT, port_call:write).
- PortCall entity: tenant_id, vessel_id, port_id, eta, etd, status, created_at (EDD §5.1).

## Acceptance criteria

- [ ] All port call operations tenant-scoped; vessel and port belong to tenant or are allowed by model.
- [ ] List supports filters and pagination; response envelope with data + meta (total, page, per_page).
