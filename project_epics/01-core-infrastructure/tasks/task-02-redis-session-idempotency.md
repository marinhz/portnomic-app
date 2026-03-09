# Task 1.2 — Redis setup for session and idempotency keys

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Configure Redis for auth session storage and idempotency keys; optional cache-aside for reference data keyed by `tenant_id`.

## Scope

- Session storage for refresh tokens or session data (if used).
- Idempotency keys to prevent duplicate operations.
- Optional: cache-aside for ports/tariffs keyed by `tenant_id` (EDD §4.3).

## Acceptance criteria

- [ ] Redis connection configured and used for session/idempotency.
- [ ] Cache keys never omit `tenant_id` where data is tenant-scoped.
- [ ] Connection failure handled gracefully (e.g. health check, timeouts).
