# Task 4.13 — Structured logging and key metrics for beta

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Structured JSON logging with request_id, tenant_id, user_id, correlation_id; key metrics for beta (request rate, latency, error rate, AI parse, queue depth) (EDD §11.1, §11.2).

## Scope

- **Logging:** JSON format; fields: timestamp, level, message, request_id, tenant_id, user_id, correlation_id; no passwords/tokens/PII (EDD §11.2).
- **Metrics:** Request rate, latency (p50/p95/p99), error rate by endpoint and tenant; AI parse duration and success rate; DA generation duration; DB pool and query latency; queue depth and processing lag (EDD §11.1).
- Expose metrics (e.g. /metrics for Prometheus); ensure log aggregation can consume JSON.
- Document log and metric semantics for ops.

## Acceptance criteria

- [ ] All app logs are structured JSON with required fields; no sensitive data.
- [ ] Key metrics are scraped or exposed; dashboards can be built for beta.
- [ ] Log and metric documentation is available for beta ops.
