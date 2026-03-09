# DevOps Agent — ShipFlow AI

Applies to CI/CD, Kubernetes, Terraform, observability, and infrastructure.

## CI/CD

- **Pipeline:** GitHub Actions or GitLab CI.
- **Steps:** Lint, unit tests, integration tests (e.g. Testcontainers), build Docker image, push to registry, deploy (dev/staging/prod).
- **Secrets:** From CI secrets store only; never in repo.
- **Deploy:** Kubernetes apply (kubectl/Helm) or GitOps (Argo CD/Flux).

## Deployment Topology

- **Cluster:** Kubernetes; namespaces per environment.
- **Backend:** Deployment, multiple replicas; HPA; readiness/liveness probes.
- **Workers:** Separate Deployment for async jobs; scale by queue depth.
- **PostgreSQL:** Primary + read replicas; write to primary only.
- **Redis:** Cache + queue.
- **Ingress:** TLS termination, rate limiting, route to backend.

## Infrastructure as Code

- **Terraform:** Modules for network, cluster, DB, Redis, DNS, certificates.
- **Environments:** Separate state or workspaces for dev, staging, prod.
- **Changes:** Review and apply via pipeline; destructive changes require approval.

## Observability

- **Metrics:** Prometheus scrape; Grafana dashboards (request rate, latency p50/p95/p99, error rate by endpoint/tenant; AI parse duration/success; DA generation; DB pool; queue depth).
- **Logging:** Structured JSON; timestamp, level, message, request_id, tenant_id, user_id, correlation_id; no passwords/tokens/PII.
- **Tracing:** Trace ID in headers and logs; spans for API, DB, LLM, email.
- **Health:** `/health` (liveness), `/ready` (DB + Redis + queue) for K8s probes.

## Conventions

- Secrets from Kubernetes Secrets or external secret manager; never in code or image.
- All outbound calls (DB, Redis, LLM, email) with timeouts; circuit breaker optional for external services.
