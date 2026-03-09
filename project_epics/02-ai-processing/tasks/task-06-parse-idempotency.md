# Task 2.6 — Idempotency for parse jobs

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Ensure same email_id is not processed twice; duplicate jobs must not overwrite completed result (EDD §8.2).

## Scope

- Before processing: check DB or Redis for email_id already completed (or in progress with lock).
- If already completed: skip processing, return success (idempotent).
- If in progress: skip or wait per design (e.g. distributed lock by email_id).
- After successful persist: mark email_id as processed (e.g. in DB processing_status or idempotency store).

## Acceptance criteria

- [ ] Re-enqueuing same email_id does not cause duplicate PortCall creation or overwrite of ai_raw_output.
- [ ] Concurrent jobs for same email_id are serialized or one wins and others skip.
- [ ] Idempotency key is email_id (and optionally tenant_id) as per EDD.
