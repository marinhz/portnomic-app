# Task 4.10 — Performance: DB indexes, query tuning, read replicas

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Optimize DB for NFR-2 (API latency p95 < 500 ms for read endpoints); indexes, query tuning, read replicas (EDD §2.3, §4.3).

## Scope

- **Indexes:** Review and add composite indexes (tenant_id, lookup columns); avoid full table scans on hot paths (EDD §5.3).
- **Query tuning:** Identify slow queries (e.g. via logging or APM); optimize N+1, unnecessary joins, large result sets.
- **Read replicas:** Route read-heavy endpoints to read replica(s); write to primary only (EDD §4.3).
- Measure p95 latency before/after; target < 500 ms for read endpoints (EDD §2.3).

## Acceptance criteria

- [ ] Critical read paths use indexes and tuned queries; p95 latency measured.
- [ ] Read replicas (if used) are configured and used for read-only endpoints.
- [ ] NFR-2 (p95 < 500 ms) met or improvement documented with plan to meet.
