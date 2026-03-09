# Task 2.5 — Background worker setup (Celery or ARQ)

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Run background workers that consume parse jobs from the queue, load email, call LLM, validate, and persist (EDD §4.2, §8.1).

## Scope

- Worker process(es) (Celery workers or ARQ); connect to same Redis and DB as API.
- Task: receive (email_id, tenant_id); load Email; call LLM client; validate output; persist (Task 2.9).
- Retries and failure handling (Task 2.10); timeouts for LLM and DB.
- Scale: run multiple workers; consider queue per tenant or priority if needed later.

## Acceptance criteria

- [ ] Worker starts and consumes jobs from queue; processes one email per job.
- [ ] Worker uses tenant_id for all DB access; no cross-tenant data leakage.
- [ ] Worker respects timeouts and retry configuration; failed jobs can be marked and optionally retried later.
