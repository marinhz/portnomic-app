# Task 5.5 — Prometheus and Grafana (metrics, dashboards)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Prometheus scrape and Grafana dashboards for production metrics (EDD §11.1).

## Scope

- **Prometheus:** Scrape backend and workers (e.g. /metrics); scrape interval and retention configured; store in Prometheus or long-term storage if needed.
- **Grafana:** Dashboards for key metrics: request rate, latency (p50/p95/p99), error rate by endpoint and tenant; AI parse duration and success rate; DA generation duration; DB connection pool and query latency; queue depth and processing lag (EDD §11.1).
- **Data sources:** Prometheus (and logs if Grafana is used for log panels); variables for tenant, time range.
- **Access:** Only authorized ops/support; no sensitive data in dashboard labels.

## Acceptance criteria

- [ ] Prometheus is scraping production targets; metrics are retained per policy.
- [ ] Grafana dashboards exist for key metrics and are used for operations.
- [ ] Dashboard ownership and refresh are documented.
