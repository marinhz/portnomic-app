# Task 2.4 — Parse job queue (Redis)

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Use Redis (or equivalent) as job queue for AI parse jobs; enqueue with email_id and tenant_id after ingest (EDD §8.1).

## Scope

- Queue structure: job payload with email_id, tenant_id; optional idempotency key (email_id).
- Producer: after storing Email, push job to queue (skip if idempotency says already queued/processed).
- Consumer: worker(s) pull jobs (see Task 2.6); ensure at-least-once or exactly-once semantics as designed.
- Configurable queue name and (if applicable) dead-letter queue.

## Acceptance criteria

- [ ] Ingest flow enqueues one job per new email; worker can consume and process.
- [ ] Idempotency prevents duplicate processing of same email_id (see Task 2.6).
- [ ] Queue depth observable for scaling and alerting.
