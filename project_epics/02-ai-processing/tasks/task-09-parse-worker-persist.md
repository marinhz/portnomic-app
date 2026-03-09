# Task 2.9 — Parse worker: validate and persist

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Map LLM output to domain: create/update PortCall, attach parsed data to Email (ai_raw_output, processing_status = completed or failed) (EDD §8.1).

## Scope

- After LLM response: validate against schema and business rules (currency, date range).
- Create or update PortCall (tenant_id, vessel_id/port from parsed data or link, eta/etd, etc.); resolve vessel/port from parsed refs if needed.
- Update Email: ai_raw_output = parsed JSON; processing_status = completed or failed; store error reason if failed.
- All DB writes scoped by tenant_id; audit or log for traceability.

## Acceptance criteria

- [ ] PortCall is created or updated with parsed vessel/port/dates; Email updated with ai_raw_output and status.
- [ ] Validation failures set processing_status = failed and store reason; no partial corrupt data.
- [ ] Tenant isolation is preserved in all writes.
