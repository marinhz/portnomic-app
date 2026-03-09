# Task 1.3 — API gateway (FastAPI)

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Implement API gateway concerns: routing, CORS, rate limiting, and request ID on all requests (EDD §4.2).

## Scope

- FastAPI app with modular routing (e.g. by domain).
- CORS whitelist for frontend origins only (EDD §6.3).
- Rate limiting per tenant and/or per user on auth and API endpoints.
- Request ID (and optionally correlation_id) on each request for tracing.

## Acceptance criteria

- [ ] All API routes mounted under versioned prefix (e.g. `/api/v1/`).
- [ ] CORS restricted to configured frontend origins.
- [ ] Rate limiting applied; 429 returned when exceeded.
- [ ] Request ID present in response headers and/or logs.
