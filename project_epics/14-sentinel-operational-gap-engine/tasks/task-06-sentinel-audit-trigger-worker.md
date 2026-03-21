# Task 14.6 — Sentinel Audit Trigger & Worker

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Integrate Sentinel audit into the ARQ worker flow. Trigger `AuditEngine.compare_events(port_call_id)` after AI parsing of a new email/file that contains relevant operational or financial data.

---

## Scope

### 1. Trigger condition

- After parse job completes for an email linked to a PortCall.
- Trigger when new data affects one of: DA line items, SOF, Noon Report, or when port call has sufficient context for AIS lookup.
- Consider: trigger on any DA/SOF/Noon document parse; or on port_call_id association.

### 2. Worker integration

- Extend ARQ worker (or add Sentinel-specific job) with payload: `port_call_id`, `tenant_id`.
- Worker loads PortCall; invokes `AuditEngine.compare_events(port_call_id)`.
- Persist Discrepancy records; no blocking of main parse flow on Sentinel failure.

### 3. Idempotency

- Use idempotency key based on `port_call_id` + document version/hash to avoid redundant audits when no new data.
- Or: run Sentinel on a schedule or on explicit "re-audit" action for a port call.

### 4. Feature gate (optional)

- Align with Epic 12 / Epic 8: Sentinel may be premium-only; check tenant plan before enqueueing.

---

## Acceptance criteria

- [ ] Sentinel audit triggers when relevant document is parsed and linked to PortCall.
- [ ] AuditEngine.compare_events invoked; Discrepancy records persisted.
- [ ] Idempotency or deduplication prevents redundant audits.
- [ ] Sentinel failure does not block core parse/ingest.

---

## Related code

- `backend/app/worker.py` — ARQ worker
- `backend/app/services/parse_worker.py` — Parse flow
- `backend/app/services/sentinel/audit_engine.py`
- Epic 12 — Leakage audit trigger (similar pattern)

---

## Dependencies

- Task 14.4 — AuditEngine
- Epic 2 — ARQ worker, parse flow
- Epic 3 — PortCall, Email, DA
