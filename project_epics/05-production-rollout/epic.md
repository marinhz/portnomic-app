# Epic 5 — Production Rollout

**Source:** SHIPFLOW_AI_Engineering_Design_Document.md, Implementation Roadmap Phase 5  
**Duration (estimate):** Ongoing

---

## Objective

Take ShipFlow AI to production: go-live, monitoring and alerting, runbooks, and support handover so the system is operable and supportable in production.

---

## Scope

### Go-live

- **Deployment:** Production environment deployed via CI/CD (Kubernetes apply or GitOps); TLS, ingress, rate limiting (EDD §10.2).
- **Secrets:** All secrets from Kubernetes Secrets or external secret manager; none in code or image (EDD §10.2, §10.1).
- **Data:** Production DB and Redis; migrations applied; backup/restore verified (EDD §10.2).
- **Cutover:** Go-live plan (DNS, traffic shift, rollback criteria); communication and support readiness.

### Monitoring and alerting

- **Metrics:** Prometheus scrape; Grafana dashboards (EDD §11.1).
- **Key metrics:** Request rate, latency p50/p95/p99, error rate by endpoint and tenant; AI parse duration and success rate; DA generation duration; DB connection pool and query latency; queue depth and processing lag (EDD §11.1).
- **Alerting:** Thresholds and alerts for availability (NFR-1 99.5%), errors, latency, queue backlog, and dependency health (EDD §2.3, §11.1).
- **Logging:** Centralized aggregation (e.g. ELK); retention and search (EDD §11.2).
- **Tracing:** Distributed tracing (trace ID in headers and logs); spans for API, DB, LLM, email (EDD §11.3).

### Resilience and operations

- **Timeouts and retries:** All outbound calls (DB, Redis, LLM, email) configured; circuit breaker optional for external services (EDD §11.4).
- **Scaling:** HPA for backend and workers; scale workers by queue depth (EDD §10.2).
- **Runbooks:** Documented procedures for common incidents (e.g. high latency, queue backlog, auth issues, LLM failures), escalation, and rollback.

### Support handover

- **Documentation:** Runbooks, architecture overview, key env vars and secrets (references only), support contacts.
- **Handover:** Knowledge transfer to support/ops; ownership of monitoring and incident response.

### Infrastructure as Code

- **Terraform:** Modules for network, cluster, DB, Redis, DNS, certificates; separate state/workspaces for dev, staging, prod (EDD §10.3).
- **Changes:** Review and apply via pipeline; destructive changes require approval (EDD §10.3).

---

## Out of scope

- New product features; this epic is about stabilisation and operations.
- Legal/commercial SLAs (EDD §1.2).

---

## Acceptance criteria

- [ ] Production environment is live; traffic served over HTTPS with correct TLS and ingress.
- [ ] Monitoring and alerting are in place; key metrics and logs are visible and alerts fire as expected.
- [ ] Runbooks exist for critical failure modes and are validated where possible.
- [ ] Support/ops have been handed over with documentation and access; escalation path is clear.
- [ ] IaC is used for production infra; changes are applied via pipeline with review.

---

## EDD references

- §2.3 Non-functional requirements (availability, latency)  
- §10 DevOps, deployment & infrastructure (CI/CD, topology, IaC)  
- §11 Observability & resilience (metrics, logging, tracing, health, timeouts, circuit breaker)
