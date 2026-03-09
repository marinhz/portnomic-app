# Task 1.7 — RBAC middleware

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Check permission for (user, resource, action) before allowing access; deny with 403 when permission is missing (EDD §6.2).

## Scope

- Permissions e.g. `vessel:read`, `vessel:write`, `port_call:read`, `port_call:write`, `admin:users`, `admin:roles` (EDD §6.2).
- FastAPI dependency that takes required permission(s) and checks current user's role against resource/action.
- Apply to all relevant route handlers.

## Acceptance criteria

- [ ] Requests without required permission return 403.
- [ ] Permission model is tenant-scoped (user's role within current tenant).
- [ ] Audit log records permission-denied events where applicable.
