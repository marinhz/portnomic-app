# Task 13.2 — PortCall Schema Extension (agent_assigned, source)

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Backend** agent with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Add `agent_assigned` and `source` (or `created_via`) fields to PortCall so manual entries can be distinguished from AI-generated ones and agents can be assigned.

---

## Scope

- Add `agent_assigned` — string or FK to User (nullable).
- Add `source` — enum or string: `"ai"` | `"manual"`; default `"manual"` for API-created, `"ai"` for parse worker.
- Update `PortCallCreate`, `PortCallUpdate`, `PortCallResponse` schemas.
- Alembic migration.
- Parse worker sets `source="ai"` when creating Port Calls.

---

## Acceptance criteria

- [ ] PortCall model has `agent_assigned` and `source` fields.
- [ ] Schemas updated; API accepts new fields.
- [ ] Parse worker sets `source="ai"` on create.
