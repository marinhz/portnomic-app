# Task 1.11 — Audit logger

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Append-only audit log for state-changing actions: who, what, when, resource_type, resource_id, and minimal context (EDD §6.4).

## Scope

- AuditLog entity: tenant_id, user_id, action, resource_type, resource_id, payload (JSON), ip, user_agent, created_at (EDD §5.1).
- Immutable store (no updates/deletes).
- Call audit logger from auth, admin, and (later) vessel, port call, DA actions.
- Structured format (e.g. JSON) for SIEM readiness.

## Acceptance criteria

- [ ] Every state-changing action (create/update/delete user, role, vessel, port call, etc.) produces an audit record.
- [ ] Records include tenant_id, user_id, action, resource_type, resource_id, timestamp; no passwords or tokens in payload.
- [ ] Logs are append-only; no API to modify or delete audit records.
