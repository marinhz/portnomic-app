# Epic 2 — AI Processing

**Source:** SHIPFLOW_AI_Engineering_Design_Document.md, Implementation Roadmap Phase 2  
**Duration (estimate):** 3 weeks

---

## Objective

Ingest operational emails, run them through an AI parsing pipeline (LLM), and persist structured maritime data (vessel, port, dates, line items, amounts) linked to tenant and port call.

---

## Scope

### Email ingest

- **Input:** IMAP poll or webhook (e.g. SendGrid Inbound) (EDD §7.4).
- **Persistence:** Store raw email with `tenant_id`, optional `port_call_id`; `processing_status = pending` (EDD §5.1 Email entity).
- **Uniqueness:** `(tenant_id, external_id)` unique to avoid duplicates (EDD §5.3).

### Queue and workers

- **Redis** (or equivalent) as job queue; enqueue job with `email_id`, `tenant_id` after ingest (EDD §8.1).
- **Background workers** (Celery/ARQ); worker picks job, loads email, calls LLM (EDD §4.2, §8.1).
- **Idempotency:** `email_id` as idempotency key; duplicate jobs must not overwrite (EDD §8.2).

### LLM integration

- **Pluggable** OpenAI-compatible API; versioned **prompt** and **output schema** (EDD §8.2).
- **Output:** Structured JSON — vessel ref, port, dates, line_items[] (description, amount, currency) (EDD §8.1).
- **Validation:** Schema validation and business rules (currency, date range) before persist (EDD §8.1).
- **Retries:** Configurable (e.g. 3) with backoff for transient LLM/network errors (EDD §8.3).
- **Failure:** After max retries, mark email `failed`, store error reason, alert; support manual override (EDD §8.3).

### Persist and link

- Map LLM output to domain: create/update **PortCall**, attach parsed data to **Email** (`ai_raw_output`, `processing_status = completed` or `failed`) (EDD §8.1).
- Optional: webhook or event for UI refresh (EDD §8.1).

### API

- **POST /ai/parse** — Submit email for parsing (or enqueue); returns job id or 202 (EDD §7.2).
- **GET /ai/parse/{job_id}** — Status/result of parse job (JWT, `ai:parse`).

### Frontend (if in scope for this epic)

- Trigger parse (e.g. from email list or port call view); show job status and parsed result.

---

## Out of scope

- DA generation, PDF, email dispatch (Epic 3).
- Full tariff/formula engine (Epic 3).

---

## Acceptance criteria

- [ ] Emails are ingested via IMAP or webhook, stored with tenant and optional port call link.
- [ ] Each new email is enqueued once; idempotency prevents duplicate processing.
- [ ] Worker calls LLM with versioned prompt and schema; output is validated and persisted.
- [ ] PortCall is created/updated and Email is updated with `ai_raw_output` and `processing_status`.
- [ ] Failed jobs are retried then marked failed with reason; operator can correct or mark invalid.
- [ ] API allows submitting an email for parse and polling job status/result with proper auth and RBAC.

---

## EDD references

- §4.4 AI processing layer  
- §5.1 Email, PortCall entities; §5.3 indexing  
- §7.2 /ai/parse endpoints  
- §8 AI processing pipeline (flow, prompt & schema, failure handling)
