# Architecture Overview

**Last updated:** March 2026

## System Diagram

```
                         ┌──────────────────────────────────────┐
                         │             INTERNET                  │
                         └─────────────────┬────────────────────┘
                                           │
                                           ▼
                         ┌──────────────────────────────────────┐
                         │  AWS Route53 (DNS)                    │
                         │  shipflow.example.com                 │
                         └─────────────────┬────────────────────┘
                                           │
                                           ▼
                         ┌──────────────────────────────────────┐
                         │  NGINX Ingress Controller             │
                         │  TLS termination (cert-manager)       │
                         │  Rate limiting (50 rps)               │
                         └──────┬───────────────────┬───────────┘
                                │                   │
                        /api, /webhooks,         / (all other)
                        /health, /ready,
                        /metrics
                                │                   │
                                ▼                   ▼
               ┌─────────────────────┐   ┌──────────────────────┐
               │  Backend (FastAPI)  │   │  Frontend (React/    │
               │  Deployment: 3 pods │   │  Nginx)              │
               │  Port: 8000         │   │  Deployment: 2 pods  │
               │  HPA: 2–10 replicas │   │  Port: 80            │
               │  Image: ghcr.io/    │   │  Image: ghcr.io/     │
               │   shipflow/backend  │   │   shipflow/frontend  │
               └──┬──┬──┬──┬──┬─────┘   └──────────────────────┘
                  │  │  │  │  │
     ┌────────┬──┘  │  │  │  └────────────┐
     │        │     │  │  │               │
     ▼        ▼     ▼  │  ▼               ▼
┌────────┐ ┌─────┐ ┌───┴──────┐   ┌─────────────┐
│Postgres│ │Redis│ │OpenAI API│   │ SMTP (SES)  │
│ 16     │ │ 7   │ │gpt-4o-   │   │ Port 587    │
│RDS     │ │Cache│ │mini      │   └─────────────┘
│Primary │ │Queue│ └──────────┘
│+ Read  │ │     │
│Replica │ │     │      ┌───────────────┐
└────────┘ └──┬──┘      │  S3 Storage   │
              │         │  PDFs, backups│
              │         └───────────────┘
              │
              ▼
     ┌──────────────────────┐
     │  Worker (ARQ)        │
     │  Deployment: 2 pods  │
     │  HPA: 2–8 replicas   │
     │  Same image as       │
     │  backend, different  │
     │  entrypoint          │
     │                      │
     │  Connects to:        │
     │  - Redis (queue)     │
     │  - PostgreSQL (R/W)  │
     │  - OpenAI (LLM)     │
     │  - S3 (PDF storage)  │
     │  - IMAP (email poll) │
     └──────────────────────┘
```

## Components

| Component | Technology | Namespace | Image | Replicas (prod) |
|-----------|-----------|-----------|-------|-----------------|
| Backend API | FastAPI, Python 3.11, Uvicorn | `shipflow` | `ghcr.io/shipflow/backend` | 3 (HPA 2–10) |
| Worker | ARQ, Python 3.11 | `shipflow` | `ghcr.io/shipflow/backend` | 2 (HPA 2–8) |
| Frontend | React 18, TypeScript, Nginx | `shipflow` | `ghcr.io/shipflow/frontend` | 2 |
| PostgreSQL | PostgreSQL 16 (RDS) | External (AWS) | Managed | Primary + read replica |
| Redis | Redis 7 (ElastiCache) | External (AWS) | Managed | Single node / cluster |
| Ingress | NGINX Ingress Controller | `ingress-nginx` | Community image | 2 |

## Data Flow: Email Ingestion to DA Generation

```
1. Email arrives
   ├── IMAP poll (worker, every 60s)
   └── POST /webhooks/inbound-email (signed webhook)
         │
         ▼
2. Email persisted to PostgreSQL
   processing_status = "pending"
   Job enqueued to Redis list: shipflow:parse_jobs
         │
         ▼
3. Worker picks job from Redis (BLPOP)
   Payload: "{job_id}:{email_id}:{tenant_id}"
         │
         ▼
4. Worker calls OpenAI API (gpt-4o-mini)
   - Circuit breaker protects against cascading failures
   - Retries: up to 3 with exponential backoff
   - Timeout: 60s per call
         │
         ▼
5. LLM returns structured JSON
   (vessel ref, port, dates, line items, amounts, currency)
         │
         ▼
6. Worker validates output, persists to DB
   - Links parsed data to Email, Port Call, Vessel
   - processing_status = "completed" or "failed"
         │
         ▼
7. User reviews parsed data in UI
   Can trigger DA generation:
   POST /api/v1/da/generate → Proforma or Final DA
         │
         ▼
8. DA approved → PDF generated → Email dispatched via SMTP
   PDF stored in S3; immutable audit trail recorded
```

## Key Design Decisions

### Multi-Tenant Isolation
Every tenant-scoped table includes a `tenant_id` UUID column. All queries are filtered by the authenticated user's tenant. Tenant is resolved from the JWT claim in FastAPI middleware — no cross-tenant access is possible at the application layer.

### Authentication
- JWT access tokens (15 min TTL) + refresh tokens (7 days)
- MFA via TOTP with AES-encrypted secrets stored in PostgreSQL
- RBAC with granular permissions: `vessel:read`, `vessel:write`, `port_call:read`, `da:approve`, `admin:users`, etc.
- Rate limiting: 100 req/min general, 20 req/min on auth endpoints

### Async Processing
Long-running work (AI email parsing, PDF generation, email dispatch) is offloaded to ARQ workers via a Redis queue (`shipflow:parse_jobs`). This keeps API response times low (p95 < 500ms target for read endpoints) while AI operations can take up to 30s.

### Resilience
- Circuit breaker on the LLM client (5 failures → open, 30s recovery, 3 half-open probes)
- Exponential backoff retries for transient errors
- Liveness (`/health`) and readiness (`/ready` — checks DB, Redis, queue) probes on all pods
- Pod Disruption Budgets: minimum 1 available pod for backend and worker during node maintenance

### Observability Stack
- **Metrics**: Prometheus scraping `/metrics` endpoint — custom counters, histograms, gauges for HTTP, auth, AI, DB, and queue metrics
- **Logging**: Structured JSON via Loki — fields include `request_id`, `tenant_id`, `user_id`, `correlation_id`
- **Tracing**: OpenTelemetry with OTLP exporter — spans for FastAPI, SQLAlchemy, Redis auto-instrumented
- **Dashboards**: Grafana with panels for request rate, latency, error rate, AI parse performance, queue depth
- **Alerting**: Alertmanager routing to Slack (warnings) and PagerDuty (critical)

## Network Architecture

Network policies enforce strict pod-to-pod communication:

- Default deny all ingress in `shipflow` namespace
- Frontend accepts ingress only from `ingress-nginx` namespace (port 80)
- Backend accepts ingress from `ingress-nginx` (port 8000) and frontend pods (port 8000)
- Backend egress allowed to: PostgreSQL (5432), Redis (6379), DNS (53), external HTTPS (443), SMTP (587), IMAP (993)
- Worker egress allowed to: PostgreSQL (5432), Redis (6379), DNS (53), external HTTPS (443), IMAP (993)

## Infrastructure

- **Compute**: AWS EKS (managed Kubernetes)
- **IaC**: Terraform modules for VPC, EKS cluster, RDS, ElastiCache, Route53, S3, IAM
- **CI/CD**: GitHub Actions → build Docker images → push to GHCR → deploy via `kubectl apply -k k8s/overlays/production`
- **TLS**: cert-manager with Let's Encrypt (`letsencrypt-prod` ClusterIssuer)
- **Secrets**: Kubernetes Secrets (recommended: Sealed Secrets or external-secrets-operator for GitOps)
- **Backups**: Daily PostgreSQL dump to S3 via CronJob at 02:00 UTC
