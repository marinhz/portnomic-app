# Task 13.6 — AuditLog Parity for Manual Port/PortCall Actions

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Backend** agent with **fastapi-python** skills.

---

## Objective

Ensure manual Port and PortCall create/update actions trigger the same AuditLog events as AI-generated ones. Port routers may already log; verify PortCall create includes `source` in payload.

---

## Scope

- Port create/update: Verify `audit_svc.log_action` with `resource_type="port"`, `action="create"`/`"update"`.
- PortCall create/update: Verify `audit_svc.log_action` with `resource_type="port_call"`, `action="create"`/`"update"`.
- Payload should include `source` (manual/ai) when applicable for PortCall.
- Ensure AI parse worker also logs PortCall create with `source="ai"` in payload for consistency.

---

## Acceptance criteria

- [ ] Manual Port create/update logged in AuditLog.
- [ ] Manual PortCall create/update logged with `source="manual"` in payload.
- [ ] AI-created PortCalls logged with `source="ai"` for parity.
