# Task 1.8 — Vessel service and API

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

CRUD for vessels, tenant-scoped; all queries filtered by tenant_id (EDD §4.2, §7.2).

## Scope

- **GET /vessels** — List vessels (tenant), pagination.
- **POST /vessels** — Create vessel (JWT, vessel:write).
- **GET /vessels/{id}** — Get vessel (JWT, vessel:read).
- **PUT /vessels/{id}** — Update vessel (JWT, vessel:write).
- Service and repository layer; vessel entity: tenant_id, name, IMO, MMSI, type, etc. (EDD §5.1).

## Acceptance criteria

- [ ] All vessel operations respect tenant; no cross-tenant read/write.
- [ ] Create/update validated with Pydantic; 404 for missing id within tenant.
