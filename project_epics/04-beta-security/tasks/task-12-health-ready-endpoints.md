# Task 4.12 — Health and readiness endpoints

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Expose `/health` (liveness) and `/ready` (DB + Redis + queue connectivity) for Kubernetes probes (EDD §11.4).

## Scope

- **GET /health** — Liveness: process is up; minimal checks (e.g. 200 OK).
- **GET /ready** — Readiness: DB connection ok, Redis ok, queue (e.g. Redis queue) reachable; return 503 if any dependency down.
- Use in K8s livenessProbe and readinessProbe; do not expose sensitive info in response body.
- Timeouts on dependency checks to avoid hanging probes.

## Acceptance criteria

- [ ] /health returns 200 when process is running; K8s can use for liveness.
- [ ] /ready returns 200 when DB, Redis, and queue are reachable; 503 otherwise; K8s can use for readiness.
- [ ] Probe response time is bounded (e.g. < 5 s).
