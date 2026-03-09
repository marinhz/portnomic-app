# Task 5.8 — Distributed tracing

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Distributed tracing: trace ID in headers and logs; spans for API, DB, LLM, email (EDD §11.3).

## Scope

- **Trace ID:** Generated at entry (API or worker); propagated in headers (e.g. X-Trace-ID, W3C Trace Context); included in logs (EDD §11.3).
- **Spans:** Instrument API handlers, DB calls, Redis, LLM client, email client; send spans to tracing backend (e.g. Jaeger, Tempo, or cloud tracer).
- **Use:** Debug latency and dependency failures across services; correlate with logs via trace ID.
- **Sampling:** Optional sampling in production to control volume and cost; 100% in staging for debugging.
- **Documentation:** How to find trace by request_id or trace_id; how to interpret spans.

## Acceptance criteria

- [ ] Trace ID is present in requests and logs; spans are sent to tracing backend.
- [ ] Ops can trace a request across API, DB, and external calls; latency breakdown is visible.
- [ ] Sampling and retention are configured; documentation is available.
