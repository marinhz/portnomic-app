# Runbooks Index

Operational runbooks for ShipFlow AI production incidents. Each runbook is self-contained and written for engineers who may not be familiar with the codebase.

**Namespace:** `shipflow`
**Grafana:** `https://grafana.shipflow.example.com`
**Alertmanager:** `https://alertmanager.shipflow.example.com`

## Runbooks

| Runbook | Alerts Covered | When to Use |
|---------|---------------|-------------|
| [High Error Rate](high-error-rate.md) | `HighErrorRate`, `HighP95Latency` | 5xx spike, elevated latency, user-reported failures |
| [Queue Backlog](queue-backlog.md) | `QueueBacklog`, `QueueBacklogCritical` | Parse jobs piling up, AI processing stalled |
| [Database Issues](database-issues.md) | `DatabaseDown`, `HighDBLatency` | Connection timeouts, slow queries, `/ready` returning 503 |
| [Auth Failures](auth-failures.md) | `HighLoginFailureRate`, `PermissionDeniedSpike` | Login failures, permission errors, suspected brute force |
| [LLM Failures](llm-failures.md) | `AIParseSlowness`, dependency alerts | AI parse failures, circuit breaker open, OpenAI outage |
| [Deployment Rollback](deployment-rollback.md) | N/A (procedural) | Rolling back a bad deployment, DNS revert, migration revert |
| [Scaling](scaling.md) | N/A (procedural) | Manual scaling, HPA tuning, queue-based scaling, DB scaling |

## Quick Reference

### Check system health

```bash
# All pods status
kubectl get pods -n shipflow

# Readiness (returns 503 if degraded)
curl -s https://shipflow.example.com/ready | jq .

# Recent pod restarts
kubectl get pods -n shipflow -o custom-columns="NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,LAST_RESTART:.status.containerStatuses[0].lastState.terminated.finishedAt"
```

### Check logs (Loki via Grafana)

```
{namespace="shipflow"} | json | level="ERROR" | line_format "{{.timestamp}} {{.message}}"
```

### Check recent deployments

```bash
kubectl rollout history deployment/backend -n shipflow
kubectl rollout history deployment/worker -n shipflow
kubectl rollout history deployment/frontend -n shipflow
```

## Escalation Path

1. **On-call engineer** — first responder, follows runbook
2. **Engineering lead** — escalate if not resolved in 15 min or if rollback is needed
3. **Engineering manager** — escalate for customer-facing outages or data integrity issues
4. **Security team** — escalate for auth anomalies or suspected breach
5. **AWS support** — escalate for RDS, ElastiCache, or EKS platform issues
