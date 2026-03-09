# Task 1.10 — Admin service and API (users, roles)

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

User and role CRUD, tenant-scoped; only accessible with admin permissions (EDD §4.2, §7.2).

## Scope

- **GET /admin/users** — List users (tenant) (JWT, admin:users).
- **POST /admin/users** — Create user (JWT, admin:users).
- **GET /admin/roles** — List roles (JWT, admin:roles).
- Extend as needed: GET/PUT /admin/users/{id}, role assignment.
- Admin service uses same tenant middleware; no cross-tenant access.

## Acceptance criteria

- [ ] Only users with admin:users / admin:roles can access; others get 403.
- [ ] All data scoped to current tenant; new users assigned to current tenant.
