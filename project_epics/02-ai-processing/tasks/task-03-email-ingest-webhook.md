# Task 2.3 — Email ingest: webhook (e.g. SendGrid Inbound)

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Accept inbound emails via webhook (e.g. SendGrid Inbound); persist and enqueue for AI parse (EDD §7.4).

## Scope

- **POST** endpoint (e.g. /webhooks/inbound-email) that receives webhook payload.
- Resolve tenant (e.g. from destination address or config); parse subject, body, received_at, unique external_id.
- Store Email (tenant_id, external_id, ...); processing_status = pending; enqueue parse job.
- Verify webhook signature if provider supports it; return 2xx quickly to avoid provider retries.

## Acceptance criteria

- [ ] Inbound webhook creates Email and enqueues parse job; tenant resolved correctly.
- [ ] Duplicate external_id per tenant does not create duplicate Email or job.
- [ ] Endpoint is idempotent and returns success within timeout expected by provider.
