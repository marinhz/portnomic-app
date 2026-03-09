# Runbook: High Error Rate / High Latency

## Alerts

- **HighErrorRate** — 5xx error rate exceeds 5% of total requests for 5 minutes
- **HighP95Latency** — P95 request latency exceeds 2 seconds for 5 minutes

## Symptoms

- Users reporting "something went wrong" or slow page loads
- Grafana HTTP Overview dashboard shows elevated 5xx responses
- Alertmanager firing `HighErrorRate` or `HighP95Latency`
- `/ready` endpoint returning 503

## Diagnosis

### 1. Check Grafana Error Rate Panel

Open **HTTP Overview** dashboard. Look at:

- `rate(http_requests_total{status_code=~"5.."}[5m])` — 5xx rate by endpoint
- `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))` — P95 latency

Identify which endpoints are affected and whether the error is localized or systemic.

### 2. Check Readiness

```bash
curl -s https://shipflow.example.com/ready | jq .
```

If any check shows `"unavailable"`, the problem is likely a downstream dependency (DB, Redis, queue). Jump to the relevant runbook:
- Database: [database-issues.md](database-issues.md)
- Redis/Queue: [queue-backlog.md](queue-backlog.md)

### 3. Check Logs in Loki

```
{namespace="shipflow", container="backend"} | json | level="ERROR"
```

Filter to the last 15 minutes. Look for:
- Stack traces (unhandled exceptions)
- Connection errors (DB, Redis, external APIs)
- Timeout errors
- Rate limit exceeded messages

Narrow by endpoint if a specific route is failing:

```
{namespace="shipflow", container="backend"} | json | level="ERROR" | endpoint=~"/api/v1/vessels.*"
```

### 4. Check Recent Deployments

```bash
kubectl rollout history deployment/backend -n shipflow
```

If a deployment happened in the last 30 minutes, it is the most likely cause.

### 5. Check Pod Status

```bash
kubectl get pods -n shipflow -l app.kubernetes.io/component=api
kubectl describe pod <pod-name> -n shipflow
kubectl logs <pod-name> -n shipflow --tail=100
```

Look for OOMKilled, CrashLoopBackOff, or failed readiness probes.

## Mitigation

### If caused by a recent deployment

```bash
kubectl rollout undo deployment/backend -n shipflow
kubectl rollout status deployment/backend -n shipflow
```

See [deployment-rollback.md](deployment-rollback.md) for full procedure.

### If a downstream dependency is down

| Dependency | Check | Runbook |
|-----------|-------|---------|
| PostgreSQL | `curl -s https://shipflow.example.com/ready \| jq .checks.database` | [database-issues.md](database-issues.md) |
| Redis | `curl -s https://shipflow.example.com/ready \| jq .checks.redis` | [queue-backlog.md](queue-backlog.md) |
| OpenAI LLM | Check `circuit_breaker_state{name="llm"}` in Grafana | [llm-failures.md](llm-failures.md) |

### If caused by a traffic spike

```bash
# Check HPA status
kubectl get hpa -n shipflow

# Check current replica count
kubectl get deployment/backend -n shipflow

# Manual scale if HPA hasn't caught up
kubectl scale deployment/backend -n shipflow --replicas=6
```

### If cause is unclear

1. Restart backend pods (rolling restart preserves availability):

```bash
kubectl rollout restart deployment/backend -n shipflow
```

2. Watch logs during restart for startup errors
3. If error persists, escalate

## Escalation

If not resolved within **15 minutes**, page the engineering lead via PagerDuty.

Provide:
- Time the alert fired
- Which endpoints are affected
- Error messages from Loki
- Actions already taken
