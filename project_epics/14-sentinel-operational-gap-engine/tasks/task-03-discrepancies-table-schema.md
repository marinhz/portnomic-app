# Task 14.3 — discrepancies Table Schema

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Create the `discrepancies` table and persistence layer for storing Sentinel audit findings. Distinct from Epic 12's `Anomaly` table; discrepancies capture cross-source operational gaps with estimated loss and source document links.

---

## Scope

### 1. New model: `Discrepancy`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK to Tenant |
| `port_call_id` | UUID | FK to PortCall |
| `source_documents` | ARRAY[UUID] | Links to conflicting emails/files |
| `severity` | enum | `low`, `medium`, `high` |
| `estimated_loss` | Decimal, nullable | Estimated Euro amount of overcharge |
| `description` | text | AI-generated explanation of the gap |
| `rule_id` | str, nullable | Sentinel rule: S-001, S-002, S-003 |
| `raw_evidence` | JSONB, nullable | Supporting data (vendor claims vs operational reality) |
| `created_at` | datetime | |

### 2. Alembic migration

- Create `discrepancies` table with FKs and indexes.
- Index on `(tenant_id, port_call_id)` for quick lookup.
- Index on `(tenant_id, severity)` for filtering high-risk items.

### 3. Schemas

- `DiscrepancyCreate` — internal use by AuditEngine.
- `DiscrepancyResponse` — for API/frontend; includes severity, description, estimated_loss, source_documents, rule_id, raw_evidence.

### 4. API endpoint

- `GET /api/port-calls/{port_call_id}/discrepancies` — List discrepancies for a port call (tenant-scoped).
- Returns `List[DiscrepancyResponse]` for SentinelAlert and SideBySideAudit components.

---

## Acceptance criteria

- [ ] `discrepancies` table exists with correct columns and FKs.
- [ ] Migration runs cleanly; no destructive changes.
- [ ] `source_documents` stored as PostgreSQL UUID array.
- [ ] Pydantic schemas support create and response.
- [ ] GET /api/port-calls/{port_call_id}/discrepancies returns tenant-scoped discrepancy list.

---

## Related code

- `backend/app/models/discrepancy.py` — Discrepancy model
- `backend/app/schemas/discrepancy.py` — Pydantic schemas
- `backend/alembic/versions/` — migration

---

## Dependencies

- Epic 1 — Tenant, PortCall models
- Epic 3 — DisbursementAccount, Email (for source_documents references)
