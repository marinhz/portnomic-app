# Task 4.11 — Performance: Redis cache-aside, worker scaling

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Use Redis cache-aside for reference data (ports, tariffs) keyed by tenant_id; scale workers and tune queue for AI parse latency NFR-3 (EDD §4.3, §2.3).

## Scope

- **Cache-aside:** Cache ports, tariffs (and other reference data) in Redis keyed by tenant_id; invalidate on update; reduce DB load on list/detail (EDD §4.3).
- **Worker scaling:** Scale worker count or concurrency so queue depth and AI parse p95 stay within NFR-3 (< 30 s per email where possible) (EDD §2.3).
- **Queue tuning:** Batch size, prefetch, timeouts; avoid starvation and backlog.
- Measure AI parse duration and queue depth; document scaling approach.

## Acceptance criteria

- [ ] Reference data endpoints benefit from cache where applicable; cache keys include tenant_id.
- [ ] Worker scaling and queue tuning reduce backlog; AI parse p95 measured and improved toward NFR-3.
- [ ] Scaling and tuning choices are documented.
