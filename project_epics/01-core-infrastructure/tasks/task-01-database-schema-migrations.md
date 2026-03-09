# Task 1.1 — Database schema and Alembic migrations

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Set up PostgreSQL as primary store with Alembic migrations for core entities and composite indexes. All tenant-scoped tables must include `tenant_id`.

## Scope

- **Entities:** Tenant, User, Role, Vessel, Port, PortCall (EDD §5.1).
- **Indexes:** Composite `(tenant_id, <main_lookup>)` e.g. `(tenant_id, created_at)`, `(tenant_id, port_call_id)` (EDD §5.3).
- **Migrations:** Versioned Alembic migrations; no destructive changes without explicit flow.

## Acceptance criteria

- [ ] Alembic initialized and first migration creates Tenant, User, Role, Vessel, Port, PortCall tables with correct columns and relationships.
- [ ] Every tenant-scoped table has `tenant_id` and appropriate composite indexes.
- [ ] Migrations run cleanly up and (where applicable) down in dev.

## Notes

- User: tenant_id, email, password_hash, mfa_secret (encrypted), role_id, created_at, last_login_at.
- Role: tenant_id, name, permissions (JSON or relation).
