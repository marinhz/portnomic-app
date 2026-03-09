# Task 1.17 — Admin UI (user/role management)

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Tenant-scoped user and role management UI; only visible and usable by users with admin permissions (EDD §4.1).

## Scope

- **Users:** List users, create user, edit user (e.g. role assignment); call GET/POST /admin/users (and PUT if implemented).
- **Roles:** List roles; call GET /admin/roles.
- UI elements gated by admin:users / admin:roles; 403 from API handled gracefully.
- RBAC-driven: admin section only shown to users with admin permissions.

## Acceptance criteria

- [ ] Admins can list and create users and assign roles within the tenant.
- [ ] Non-admins do not see or cannot access admin section; API returns 403 when appropriate.
- [ ] Forms validate input and display API errors; success feedback on create/update.
