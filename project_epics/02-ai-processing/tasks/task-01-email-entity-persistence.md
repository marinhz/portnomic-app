# Task 2.1 — Email entity and persistence

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Add Email entity and persistence: store raw email with tenant_id, optional port_call_id, processing_status; enforce uniqueness to avoid duplicates (EDD §5.1, §5.3).

## Scope

- **Email:** id, tenant_id, port_call_id (nullable), external_id, subject, body_text, body_html, received_at, processing_status, ai_raw_output (JSON), created_at.
- **Unique:** (tenant_id, external_id); index (tenant_id, processing_status) for queue consumers (EDD §5.3).
- Alembic migration for Email table.

## Acceptance criteria

- [ ] Email can be stored with required fields; processing_status defaults to pending.
- [ ] Duplicate (tenant_id, external_id) is rejected or skipped (e.g. unique constraint).
- [ ] Queries by tenant_id and processing_status are indexed.
