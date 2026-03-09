# Go-Live Plan

**Last updated:** March 2026

## Pre-Go-Live Checklist

Complete every item before proceeding with the cutover. Each item requires a sign-off from the responsible owner.

| # | Item | Owner | Verified |
|---|------|-------|----------|
| 1 | Terraform applied to production — EKS cluster, RDS, ElastiCache, S3, Route53, IAM roles all provisioned | DevOps | [ ] |
| 2 | Database migrations applied (`alembic upgrade head`) and verified against expected schema | Backend | [ ] |
| 3 | Daily DB backup CronJob running (`db-backup` in `shipflow` namespace), test restore completed successfully | DevOps | [ ] |
| 4 | All secrets rotated from dev/staging values — `JWT_SECRET`, `MFA_ENCRYPTION_KEY`, `LLM_API_KEY`, `WEBHOOK_INBOUND_SECRET`, `STORAGE_S3_*`, `SMTP_*`, `IMAP_PASSWORD`, `DATABASE_URL`, `REDIS_URL` | Security | [ ] |
| 5 | Prometheus scraping backend `/metrics`, Grafana dashboards loaded, Alertmanager routing to Slack + PagerDuty confirmed | DevOps | [ ] |
| 6 | Loki receiving structured logs from all pods; test query: `{namespace="shipflow"} \| json \| level="ERROR"` returns results | DevOps | [ ] |
| 7 | OpenTelemetry exporter connected (`OTEL_ENABLED=true`); traces visible in tracing backend | DevOps | [ ] |
| 8 | All runbooks reviewed by on-call team (see [Runbook Index](runbooks/README.md)) | Engineering | [ ] |
| 9 | On-call rotation set up in PagerDuty; at least 2 engineers on rotation | Engineering | [ ] |
| 10 | Network policies applied — verify frontend, backend, and worker pods can only reach intended targets | DevOps | [ ] |
| 11 | TLS certificate issued via cert-manager; `kubectl get certificate -n shipflow` shows `Ready=True` | DevOps | [ ] |
| 12 | Rate limiting active on ingress (50 rps) and application level (100 req/min general, 20 req/min auth) | Backend | [ ] |
| 13 | Pod Disruption Budgets applied (`backend-pdb`, `worker-pdb`) with `minAvailable: 1` | DevOps | [ ] |
| 14 | HPA configured — backend (2–10 replicas, 70% CPU), worker (2–8 replicas, 70% CPU) | DevOps | [ ] |
| 15 | IMAP credentials configured and polling verified (if applicable) | Backend | [ ] |
| 16 | SMTP configured and test email sent successfully | Backend | [ ] |
| 17 | S3 bucket lifecycle rules set for backup retention | DevOps | [ ] |

---

## DNS Cutover

### Preparation (24h before)

1. Lower TTL on the existing DNS record to **300 seconds** (5 min) to allow fast failover:

```bash
aws route53 change-resource-record-sets --hosted-zone-id <ZONE_ID> --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "shipflow.example.com",
      "Type": "A",
      "TTL": 300,
      "AliasTarget": {
        "HostedZoneId": "<CURRENT_ALB_ZONE_ID>",
        "DNSName": "<CURRENT_ALB_DNS>",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'
```

2. Verify TTL propagation:

```bash
dig shipflow.example.com +short
dig shipflow.example.com +norecurse +nssearch
```

### Cutover

Update the A record (or Alias) to point to the production EKS ingress load balancer:

```bash
aws route53 change-resource-record-sets --hosted-zone-id <ZONE_ID> --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "shipflow.example.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "<PROD_ALB_ZONE_ID>",
        "DNSName": "<PROD_ALB_DNS>",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'
```

### Post-Cutover

After confirming stability (30 min minimum), raise TTL to **3600 seconds** (1 hour):

```bash
# Update TTL to 3600 once traffic is stable
```

### Blue-Green Option (Weighted Routing)

For a gradual cutover, use weighted routing to shift traffic incrementally:

1. Create two weighted record sets (old = weight 100, new = weight 0)
2. Shift weight: 0 → 10 → 50 → 100 on the new target
3. Monitor error rates and latency at each step
4. Set old target weight to 0 once fully migrated

---

## Traffic Shift Plan

### Step 1: Deploy to Production Cluster (No External Traffic)

```bash
# Apply production overlay
kubectl apply -k k8s/overlays/production

# Verify all pods are running
kubectl get pods -n shipflow
kubectl rollout status deployment/backend -n shipflow
kubectl rollout status deployment/worker -n shipflow
kubectl rollout status deployment/frontend -n shipflow
```

### Step 2: Smoke Tests

Run these against the cluster-internal service (port-forward or via staging ingress):

```bash
# Health check
curl -sf https://shipflow.example.com/health
# Expected: {"status":"ok"}

# Readiness check
curl -sf https://shipflow.example.com/ready
# Expected: {"status":"ready","checks":{"database":"ok","redis":"ok","queue":"ok"}}

# Login
curl -sf -X POST https://shipflow.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@shipflow.ai","password":"<prod_password>"}'
# Expected: 200 with access_token

# Create vessel (with token from login)
curl -sf -X POST https://shipflow.example.com/api/v1/vessels \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Vessel","imo":"1234567"}'
# Expected: 201

# AI parse submit (with token)
curl -sf -X POST https://shipflow.example.com/api/v1/ai/parse \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"email_id":"<test_email_id>"}'
# Expected: 200/202 with job_id
```

### Step 3: Switch DNS (or LB Target)

Execute the DNS cutover as described above. If using an ALB, update the target group instead.

### Step 4: Monitor for 30 Minutes

Open the following Grafana dashboards and watch for anomalies:

- **HTTP Overview**: Request rate, error rate (5xx), P95 latency
- **AI Parse Performance**: `ai_parse_duration_seconds`, `ai_parse_total{status="error"}`
- **Queue Health**: `queue_depth{queue_name="shipflow:parse_jobs"}`
- **Database**: `db_query_duration_seconds`, connection pool utilization

Key thresholds during monitoring window:
- Error rate < 1%
- P95 latency < 500ms (API), < 30s (AI parse)
- Queue depth not growing unbounded
- No pod restarts (`kubectl get pods -n shipflow -w`)

### Step 5: Confirm or Rollback

If all metrics are healthy after 30 min:
- Confirm go-live in Slack channel
- Raise DNS TTL to 3600s
- Send post-go-live confirmation email

If rollback criteria are met — proceed to rollback procedure below.

---

## Rollback Criteria

Initiate rollback if **any** of the following conditions are met:

| Condition | Threshold | Detection |
|-----------|-----------|-----------|
| Error rate | > 5% of requests returning 5xx for 5 consecutive minutes | Grafana: `rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])` |
| P95 latency | > 2 seconds sustained for 5 minutes | Grafana: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` |
| Critical service down | PostgreSQL, Redis, or LLM unreachable | `/ready` returning 503; Alertmanager firing |
| Data corruption | Any evidence of incorrect writes, missing tenant isolation, or duplicate records | Manual verification or anomaly in audit logs |
| Worker failure | Queue depth growing > 100 with no processing | `queue_depth{queue_name="shipflow:parse_jobs"} > 100` |

**Decision maker:** On-call lead or engineering manager. If neither is reachable within 5 minutes, any engineer on the go-live team may initiate rollback.

---

## Rollback Procedure

### 1. Revert Kubernetes Deployment

```bash
# Undo the latest rollout for all components
kubectl rollout undo deployment/backend -n shipflow
kubectl rollout undo deployment/worker -n shipflow
kubectl rollout undo deployment/frontend -n shipflow

# Verify rollback
kubectl rollout status deployment/backend -n shipflow
kubectl rollout status deployment/worker -n shipflow
kubectl rollout status deployment/frontend -n shipflow
```

### 2. Revert DNS (If Changed)

```bash
# Point DNS back to the previous target
aws route53 change-resource-record-sets --hosted-zone-id <ZONE_ID> --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "shipflow.example.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "<OLD_ALB_ZONE_ID>",
        "DNSName": "<OLD_ALB_DNS>",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'
```

### 3. Revert Database Migration (If Needed)

```bash
# Roll back the last migration
kubectl exec -it deployment/backend -n shipflow -- alembic downgrade -1

# Verify schema
kubectl exec -it deployment/backend -n shipflow -- alembic current
```

### 4. Notify Stakeholders

Post in the `#shipflow-go-live` Slack channel:

> :rotating_light: **Rollback initiated** — [describe reason]. Traffic reverted to previous deployment. Investigation underway. ETA for update: [time].

### 5. Post-Incident Review

Schedule within 24 hours. Capture:
- Timeline of events
- Root cause
- What monitoring caught (or missed)
- Action items to prevent recurrence

---

## Communication Plan

### Pre-Go-Live (24h Before)

**Email to stakeholders:**
> Subject: ShipFlow AI — Production Go-Live Scheduled [DATE]
>
> We will be performing the production go-live for ShipFlow AI on [DATE] at [TIME UTC]. Expected duration: 1–2 hours. A brief period of DNS propagation (up to 5 minutes) may cause intermittent connectivity.
>
> We will post live updates in Slack: `#shipflow-go-live`

### During Go-Live

- All updates in Slack `#shipflow-go-live` channel
- Status page updated to "Maintenance" (if applicable)
- On-call team available on a dedicated voice/video call

### Post-Go-Live Confirmation

**Email to stakeholders:**
> Subject: ShipFlow AI — Production Go-Live Complete
>
> The production go-live completed successfully at [TIME UTC]. All systems are operational. Monitoring is active.
>
> Dashboard: [Grafana URL]
> Status: [status page URL]

---

## Post-Go-Live Monitoring

| Period | Action |
|--------|--------|
| First 2 hours | Dedicated engineer watching Grafana dashboards. Immediate response to any alert. |
| First 24 hours | Heightened alerting thresholds (lower error rate trigger: 2% instead of 5%). Dedicated on-call engineer. |
| First 48 hours | Two engineers on on-call rotation. Review all alerts, even informational. |
| Day 1 standup | Review first 24h metrics: request volume, error rate, P95 latency, AI parse success rate, queue throughput. |
| Day 7 standup | Comprehensive review: resource utilization, cost, scaling events, user-reported issues, alert noise. |
| First week | Daily 15-min standup for ops review. Adjust alerting thresholds and HPA settings based on real traffic patterns. |

### Key Metrics to Review at 24h and 7d

- `http_requests_total` — total request volume and error breakdown
- `http_request_duration_seconds` — P50, P95, P99 latency
- `ai_parse_total` — success vs failure count
- `ai_parse_duration_seconds` — parse latency distribution
- `queue_depth` — average and peak queue depth
- `db_query_duration_seconds` — slow query trends
- `auth_login_attempts_total` — login volume and failure rate
- Pod restart count: `kubectl get pods -n shipflow` (RESTARTS column)
- HPA scaling events: `kubectl describe hpa -n shipflow`
- Node resource utilization in AWS console
