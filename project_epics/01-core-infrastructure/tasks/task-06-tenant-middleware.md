# Task 1.6 — Tenant middleware

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Resolve tenant from JWT and inject into request context so every downstream service and query can enforce tenant isolation (EDD §4.2, §3.3).

## Scope

- FastAPI dependency that reads JWT, extracts tenant_id, validates tenant exists, injects into request/context.
- All protected routes depend on this; no cross-tenant access possible when used consistently.

## Acceptance criteria

- [ ] Tenant ID available in request state/context for all authenticated requests.
- [ ] Invalid or missing tenant in JWT results in 401/403.
- [ ] Services and repositories use injected tenant_id for all tenant-scoped queries.
