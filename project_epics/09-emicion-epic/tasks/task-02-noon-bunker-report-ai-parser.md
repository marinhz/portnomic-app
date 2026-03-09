# Task 9.2 — Noon / Bunker Report AI Parser

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Implement LLM-based parsing of Noon Reports and Bunker Reports. The parser uses a dedicated prompt and the extraction schema from Task 9.1. It is triggered when the email parser detects a "Noon Report" or "Bunker Report" (e.g. via subject/body heuristics or classification).

---

## Scope

### Trigger

- **Option A:** Extend existing parse worker — add report type detection; if noon/bunker, use emission extraction prompt/schema instead of port-call schema.
- **Option B:** Separate job type — enqueue emission parse job when email matches noon/bunker pattern; worker runs emission-specific parser.
- Detection: Subject keywords ("Noon Report", "Bunker Report", "Daily Report"), body patterns, or LLM classification.

### LLM integration

- Versioned prompt for emission extraction: instructions to extract vessel (name, IMO), fuel entries (type, consumption, status), distance.
- Output validated against Task 9.1 schema.
- On success: persist EmissionReport; link to email (`ai_raw_output`, `processing_status`).
- On failure: retry (existing retry logic); mark failed with reason.

### API

- **POST /api/v1/emissions/parse** — Submit email for emission parse; returns job id (or reuse `/ai/parse` with `report_type=emission`).
- **GET /api/v1/emissions/parse/{job_id}** — Status and result.

---

## Acceptance criteria

- [ ] Noon/bunker reports are detected and routed to emission parser.
- [ ] LLM extracts structured data; output validated and persisted as EmissionReport.
- [ ] EmissionReport linked to source email for audit.
- [ ] API allows triggering emission parse and polling job status.

---

## Related code

- `backend/app/workers/emission_parse_worker.py` — or extend existing parse worker
- `backend/app/services/emission_parser.py` — prompt, schema, validation
- `backend/app/routers/emissions.py` — parse endpoints

---

## Dependencies

- Task 9.1 (extraction schema, data model).
- Epic 2 (LLM client, job queue, idempotency).
