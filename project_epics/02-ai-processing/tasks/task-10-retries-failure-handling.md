# Task 2.10 — Retries and failure handling

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Configurable retries with backoff for transient LLM/network errors; after max retries mark email failed, store reason, alert; support manual override (EDD §8.3).

## Scope

- Retries: e.g. 3 with exponential backoff; only for transient errors (network, 5xx, rate limit).
- After max retries: set Email processing_status = failed; store error message/reason; trigger alert (e.g. metric or notification).
- Manual override: API or UI for operator to correct parsed data or mark email as invalid/skip so it does not block or re-queue.
- Dead-letter or failed queue visibility for ops.

## Acceptance criteria

- [ ] Transient failures are retried; permanent failures mark email failed with reason.
- [ ] Alerts fire when emails fail after max retries (or failed count exceeds threshold).
- [ ] Operator can correct or mark invalid; no endless retry loop for same email.
