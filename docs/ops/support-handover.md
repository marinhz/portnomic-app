# Support Handover Guide

**Last updated:** March 2026

This document provides everything a support or operations engineer needs to monitor, troubleshoot, and maintain the ShipFlow AI production environment.

---

## System Overview

ShipFlow AI is a multi-tenant maritime agency SaaS platform. It ingests operational emails, uses AI (OpenAI) to parse them into structured port call data, and generates disbursement accounts (DAs) for vessel visits.

### Architecture (Simplified)

```
Internet → NGINX Ingress (TLS) → Frontend (React/Nginx, 2 pods)
                                → Backend (FastAPI, 3 pods)
                                     ├── PostgreSQL 16 (RDS)
                                     ├── Redis 7 (ElastiCache)
                                     ├── OpenAI API (LLM)
                                     ├── SMTP (email dispatch)
                                     └── S3 (PDF + backup storage)
                                → Worker (ARQ, 2 pods)
                                     ├── Redis (job queue)
                                     ├── PostgreSQL (R/W)
                                     ├── OpenAI API (AI parsing)
                                     └── IMAP (email polling)
```

See [architecture-overview.md](architecture-overview.md) for the full diagram and component details.

### Key Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Backend** | REST API, auth, business logic, RBAC | FastAPI, Python 3.11, Uvicorn |
| **Worker** | AI email parsing, IMAP polling, async jobs | ARQ, same image as backend |
| **Frontend** | User interface (SPA) | React 18, TypeScript, Nginx |
| **PostgreSQL** | Primary data store (all tenant data, users, DAs) | PostgreSQL 16, AWS RDS |
| **Redis** | Job queue (`shipflow:parse_jobs`), caching | Redis 7, AWS ElastiCache |
| **Ingress** | TLS termination, routing, rate limiting | NGINX Ingress Controller |

### Kubernetes Namespace

All ShipFlow workloads run in the `shipflow` namespace.

```bash
kubectl get all -n shipflow
```

---

## Access Required

| System | URL / Access | Credential Method | Permissions Needed |
|--------|-------------|-------------------|-------------------|
| **Grafana** | `https://grafana.shipflow.example.com` | SSO or local account | Viewer (dashboards + Loki) |
| **Prometheus** | Via Grafana data source | N/A (internal) | N/A |
| **Loki** | Via Grafana Explore | N/A (internal) | Viewer |
| **Alertmanager** | `https://alertmanager.shipflow.example.com` | SSO or local account | Viewer |
| **AWS Console** | `https://console.aws.amazon.com` | IAM role: `shipflow-ops-readonly` | Read-only (RDS, ElastiCache, EKS, S3, Route53) |
| **kubectl** | Kubeconfig from EKS | `aws eks update-kubeconfig --name shipflow-prod` | Namespace-scoped to `shipflow` |
| **GitHub** | `https://github.com/shipflow` | GitHub account | Read access to `shipflow` repo |
| **PagerDuty** | `https://shipflow.pagerduty.com` | SSO | On-call schedule access |

### Setting Up kubectl

```bash
# Configure kubectl for the production cluster
aws eks update-kubeconfig --name shipflow-prod --region <region>

# Verify access (should only see shipflow namespace resources)
kubectl get pods -n shipflow
```

---

## Environment Variables

All environment configuration is documented in `.env.example` at the project root. **Never log or share actual secret values.**

### Key Variables

| Variable | Purpose | Where Set |
|----------|---------|-----------|
| `DATABASE_URL` | PostgreSQL connection string | K8s Secret (`shipflow-secrets`) |
| `REDIS_URL` | Redis connection string | K8s Secret |
| `JWT_SECRET` | Signs JWT access/refresh tokens | K8s Secret |
| `MFA_ENCRYPTION_KEY` | Encrypts MFA TOTP secrets at rest | K8s Secret |
| `LLM_API_KEY` | OpenAI API key for AI parsing | K8s Secret |
| `LLM_MODEL` | Model used for parsing (default: `gpt-4o-mini`) | K8s ConfigMap (`shipflow-config`) |
| `LLM_TIMEOUT_SECONDS` | Max wait for LLM response (default: `60`) | K8s ConfigMap |
| `ENVIRONMENT` | `production` | K8s ConfigMap |
| `LOG_LEVEL` | `INFO` | K8s ConfigMap |
| `CORS_ORIGINS` | Allowed frontend origin | K8s ConfigMap |
| `STORAGE_BACKEND` | `s3` in production | K8s ConfigMap |
| `SMTP_*` | Email dispatch credentials | K8s Secret |
| `IMAP_*` | Email ingest credentials | K8s Secret |

### Viewing ConfigMap (non-secret values)

```bash
kubectl get configmap shipflow-config -n shipflow -o yaml
```

### Viewing Secret keys (names only, not values)

```bash
kubectl get secret shipflow-secrets -n shipflow -o jsonpath='{.data}' | jq 'keys'
```

---

## Monitoring Guide

### Grafana Dashboards

| Dashboard | What It Shows | When to Check |
|-----------|-------------|---------------|
| **HTTP Overview** | Request rate, error rate (5xx), P50/P95/P99 latency by endpoint | Any performance or error alert |
| **AI Parse Performance** | Parse duration, success/error rate, circuit breaker state | AI-related alerts or user complaints about parsing |
| **Queue Health** | `queue_depth` over time, processing rate | Queue backlog alerts |
| **Database** | Query duration by operation, connection count | DB latency or availability alerts |
| **Auth** | Login attempts, failures by reason, permission denied rate | Auth-related alerts |

### Key Panels and What They Mean

| Panel / Metric | Healthy | Warning | Critical |
|---------------|---------|---------|----------|
| `http_requests_total{status_code=~"5.."}` rate | < 1% of total | 1–5% | > 5% |
| `http_request_duration_seconds` P95 | < 500ms | 500ms–2s | > 2s |
| `ai_parse_duration_seconds` P95 | < 30s | 30–60s | > 60s or timing out |
| `queue_depth` | < 10 | 10–50 | > 50 |
| `circuit_breaker_state{name="llm"}` | 0 (closed) | 2 (half_open) | 1 (open) |
| `auth_login_failures_total` rate | Low, sporadic | Sustained increase | Rapid spike |
| `db_query_duration_seconds` P95 | < 100ms | 100ms–1s | > 1s |

### Loki Log Queries

Access via **Grafana → Explore → Loki**.

```
# All errors in the last 15 minutes
{namespace="shipflow"} | json | level="ERROR"

# Backend errors only
{namespace="shipflow", container="backend"} | json | level="ERROR"

# Worker errors only
{namespace="shipflow", container="worker"} | json | level="ERROR"

# Errors for a specific tenant
{namespace="shipflow"} | json | level="ERROR" | tenant_id="<uuid>"

# Errors with a specific request ID
{namespace="shipflow"} | json | request_id="<uuid>"

# Slow API responses (logged when > 1s)
{namespace="shipflow", container="backend"} | json | duration > 1
```

### Alertmanager

Alerts route to:
- **Slack** (`#shipflow-alerts`): Warnings and informational alerts
- **PagerDuty**: Critical alerts that require immediate action

To silence an alert during planned maintenance:

1. Open Alertmanager UI
2. Click "Silences" → "New Silence"
3. Set matchers for the alert name and duration
4. Add a comment explaining the maintenance window

---

## Common Tasks

### Restart a service

```bash
# Rolling restart (zero-downtime, PDB ensures availability)
kubectl rollout restart deployment/backend -n shipflow
kubectl rollout restart deployment/worker -n shipflow
kubectl rollout restart deployment/frontend -n shipflow

# Watch the rollout
kubectl rollout status deployment/backend -n shipflow
```

### Check logs for a specific pod

```bash
# Recent logs
kubectl logs deployment/backend -n shipflow --tail=100

# Follow logs live
kubectl logs -f deployment/backend -n shipflow

# Logs from a specific pod
kubectl logs <pod-name> -n shipflow --tail=200

# Previous container logs (if pod restarted)
kubectl logs <pod-name> -n shipflow --previous
```

### Scale pods

```bash
# Scale backend
kubectl scale deployment/backend -n shipflow --replicas=5

# Scale workers (for queue backlog)
kubectl scale deployment/worker -n shipflow --replicas=5

# Check HPA status
kubectl get hpa -n shipflow
```

### Check queue status

```bash
kubectl exec -it deployment/backend -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('Queue depth:', r.llen('shipflow:parse_jobs'))
"
```

### Verify system health

```bash
# Liveness
curl -s https://shipflow.example.com/health | jq .

# Readiness (checks DB + Redis + queue)
curl -s https://shipflow.example.com/ready | jq .
```

### Check database migration status

```bash
kubectl exec -it deployment/backend -n shipflow -- alembic current
kubectl exec -it deployment/backend -n shipflow -- alembic history --verbose
```

### Check backup status

```bash
# List recent backup jobs
kubectl get jobs -n shipflow -l app.kubernetes.io/name=db-backup

# Check latest backup job logs
kubectl logs job/db-backup-<timestamp> -n shipflow
```

---

## Incident Response

### Who to Contact

| Role | Contact | When |
|------|---------|------|
| **On-call engineer** | PagerDuty rotation | First responder for all alerts |
| **Engineering lead** | Slack DM or phone | Escalation after 15 min, rollback decisions |
| **Engineering manager** | Slack DM or phone | Customer-facing outages, data integrity |
| **Security team** | `#security-incidents` Slack channel | Auth anomalies, suspected breach |
| **AWS support** | AWS Console → Support | RDS, ElastiCache, EKS platform issues |

### SLA Expectations

| Severity | Response Time | Resolution Target | Examples |
|----------|-------------|-------------------|---------|
| **P1 — Critical** | 15 min | 1 hour | System down, data corruption, security breach |
| **P2 — High** | 30 min | 4 hours | Degraded performance, AI parsing completely down |
| **P3 — Medium** | 2 hours | 24 hours | Non-critical feature broken, intermittent errors |
| **P4 — Low** | Next business day | 1 week | Cosmetic issues, minor inconveniences |

### When to Escalate

- Runbook steps exhausted without resolution → page engineering lead
- Customer-facing outage lasting > 15 min → notify engineering manager
- Any suspected security incident → immediately notify security team
- AWS infrastructure issue → open AWS support case

---

## Runbook Index

All operational runbooks are in the `docs/ops/runbooks/` directory:

| Runbook | Description |
|---------|-------------|
| [High Error Rate](runbooks/high-error-rate.md) | 5xx spikes, high latency diagnosis and mitigation |
| [Queue Backlog](runbooks/queue-backlog.md) | Parse job queue growing, workers stalled |
| [Database Issues](runbooks/database-issues.md) | DB connectivity, slow queries, connection pool exhaustion |
| [Auth Failures](runbooks/auth-failures.md) | Login failures, permission errors, brute force response |
| [LLM Failures](runbooks/llm-failures.md) | AI parse failures, circuit breaker, OpenAI outages |
| [Deployment Rollback](runbooks/deployment-rollback.md) | Rolling back deployments, DNS, and migrations |
| [Scaling](runbooks/scaling.md) | Manual scaling, HPA tuning, DB/Redis scaling |

---

## Knowledge Transfer Checklist

Use this checklist when onboarding a new support engineer. Both the trainer and trainee should sign off on each item.

| # | Item | Trainee | Trainer | Date |
|---|------|---------|---------|------|
| 1 | Has `kubectl` access to `shipflow` namespace; can run `kubectl get pods -n shipflow` | [ ] | [ ] | |
| 2 | Has Grafana access; can navigate to HTTP Overview dashboard | [ ] | [ ] | |
| 3 | Has Grafana/Loki access; can run a basic log query: `{namespace="shipflow"} \| json \| level="ERROR"` | [ ] | [ ] | |
| 4 | Has Alertmanager access; understands alert routing (Slack vs PagerDuty) | [ ] | [ ] | |
| 5 | Has AWS Console read-only access; can view RDS and ElastiCache metrics | [ ] | [ ] | |
| 6 | Has read the [Architecture Overview](architecture-overview.md) and can describe the data flow | [ ] | [ ] | |
| 7 | Has read all runbooks in `docs/ops/runbooks/` | [ ] | [ ] | |
| 8 | Has performed a guided walkthrough: restarted a pod, checked logs, checked queue depth | [ ] | [ ] | |
| 9 | Has performed a simulated incident using one of the runbooks | [ ] | [ ] | |
| 10 | Knows the escalation path (on-call → lead → manager → security/AWS) | [ ] | [ ] | |
| 11 | Has been added to `#shipflow-alerts` and `#shipflow-ops` Slack channels | [ ] | [ ] | |
| 12 | Has been added to the PagerDuty on-call rotation | [ ] | [ ] | |
| 13 | Has GitHub read access to the `shipflow` repository | [ ] | [ ] | |
| 14 | Understands the go-live plan and rollback criteria (see [go-live-plan.md](go-live-plan.md)) | [ ] | [ ] | |
