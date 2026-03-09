# Task 5.9 — Timeouts, retries, circuit breaker

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

All outbound calls (DB, Redis, LLM, email) have timeouts and retries where appropriate; optional circuit breaker for external services (EDD §11.4).

## Scope

- **Timeouts:** DB, Redis, HTTP (LLM, email) clients have connect and read timeouts; avoid indefinite hang.
- **Retries:** Transient failures (e.g. network, 5xx) retried with backoff; permanent failures (4xx) not retried blindly.
- **Circuit breaker:** Optional for LLM and email providers to avoid cascade failures; open after N failures; half-open to retry (EDD §11.4).
- **Configuration:** Timeouts and retry counts in config; document defaults and tuning.
- **Observability:** Log or metric when timeouts/retries/circuit open occur.

## Acceptance criteria

- [ ] All outbound calls have timeouts; retries are configured for transient errors.
- [ ] Circuit breaker (if implemented) opens on repeated failure and recovers when healthy.
- [ ] Timeouts and retries are documented; tuning is possible without code change where feasible.
