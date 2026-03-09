# Task 2.2 — Email ingest: IMAP poll

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Poll IMAP mailbox(es) for new emails; persist each with tenant_id and processing_status = pending; enqueue for AI parse (EDD §7.4, §8.1).

## Scope

- IMAP client (e.g. scheduled job or long-running poll); map mailbox or config to tenant.
- For each new message: store in Email table (tenant_id, external_id from message id, subject, body, received_at, processing_status = pending).
- After persist, enqueue parse job (email_id, tenant_id) to Redis/queue.
- Idempotency: do not create duplicate Email for same (tenant_id, external_id).

## Acceptance criteria

- [ ] New emails from IMAP are stored and enqueued once per tenant/message.
- [ ] Duplicates (same message id per tenant) do not create duplicate records or jobs.
- [ ] Failures in fetch or store are logged and optionally retried without losing messages.
