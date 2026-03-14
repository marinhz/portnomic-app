# Task 12.1 — Anomaly Table & Schema

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Create the Anomaly entity and persistence layer for storing detected discrepancies from the leakage audit. Anomalies link to Email and DA entities for traceability.

---

## Scope

### 1. New model: `Anomaly`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK to Tenant |
| `email_id` | UUID | FK to Email (source document) |
| `da_id` | UUID, nullable | FK to DisbursementAccount (if DA exists) |
| `port_call_id` | UUID | FK to PortCall (context) |
| `rule_id` | str | LD-001, LD-002, LD-003, LD-004 |
| `severity` | enum | `low`, `medium`, `high`, `critical` |
| `line_item_ref` | str, nullable | Reference to line item (e.g. index or description) |
| `invoiced_value` | decimal, nullable | Value from invoice |
| `expected_value` | decimal, nullable | Value from system/operational data |
| `description` | text | Human-readable explanation |
| `raw_evidence` | JSONB, nullable | Supporting data for audit transparency |
| `created_at` | datetime | |

### 2. Alembic migration

- Create `anomalies` table with FKs and indexes.
- Index on `(tenant_id, email_id)` for quick lookup.
- Index on `(tenant_id, da_id)` for DA workspace queries.

### 3. Schemas

- `AnomalyCreate` — internal use by AuditService.
- `AnomalyResponse` — for API/frontend; includes rule_id, severity, description, invoiced_value, expected_value, line_item_ref.

---

## Acceptance criteria

- [ ] `anomalies` table exists with correct columns and FKs.
- [ ] Migration runs cleanly; no destructive changes.
- [ ] Pydantic schemas support create and response; raw_evidence optional.

---

## Related code

- `backend/app/models/` — Anomaly model
- `backend/app/schemas/` — Anomaly schemas
- `backend/alembic/versions/` — migration

---

## Dependencies

- Epic 1 — Tenant, Email, PortCall models
- Epic 3 — DisbursementAccount (DA) model
