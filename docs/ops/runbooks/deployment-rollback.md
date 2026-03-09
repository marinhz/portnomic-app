# Runbook: Deployment Rollback

## When to Use

- A deployment introduced errors (5xx spike, crashes, broken functionality)
- Go-live rollback criteria are met (see [go-live-plan.md](../go-live-plan.md))
- Need to revert to a known-good state quickly

## Check Rollout History

```bash
# View deployment history
kubectl rollout history deployment/backend -n shipflow
kubectl rollout history deployment/worker -n shipflow
kubectl rollout history deployment/frontend -n shipflow

# View details of a specific revision
kubectl rollout history deployment/backend -n shipflow --revision=3
```

## Roll Back to Previous Version

### Quick rollback (previous revision)

```bash
# Backend
kubectl rollout undo deployment/backend -n shipflow
kubectl rollout status deployment/backend -n shipflow

# Worker
kubectl rollout undo deployment/worker -n shipflow
kubectl rollout status deployment/worker -n shipflow

# Frontend
kubectl rollout undo deployment/frontend -n shipflow
kubectl rollout status deployment/frontend -n shipflow
```

### Roll back to a specific revision

```bash
# Find the target revision number from rollout history
kubectl rollout history deployment/backend -n shipflow

# Roll back to revision N
kubectl rollout undo deployment/backend -n shipflow --to-revision=N
kubectl rollout status deployment/backend -n shipflow
```

### Roll back using a specific image tag

If you know the exact image tag to revert to:

```bash
kubectl set image deployment/backend -n shipflow \
  backend=ghcr.io/shipflow/backend:v0.9.0

kubectl set image deployment/worker -n shipflow \
  worker=ghcr.io/shipflow/backend:v0.9.0

kubectl set image deployment/frontend -n shipflow \
  frontend=ghcr.io/shipflow/frontend:v0.9.0
```

## DNS Rollback

If DNS was changed during the deployment (e.g., go-live cutover):

```bash
aws route53 change-resource-record-sets --hosted-zone-id <ZONE_ID> --change-batch '{
  "Changes": [{
    "Action": "UPSERT",
    "ResourceRecordSet": {
      "Name": "shipflow.example.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "<PREVIOUS_ALB_ZONE_ID>",
        "DNSName": "<PREVIOUS_ALB_DNS>",
        "EvaluateTargetHealth": true
      }
    }
  }]
}'
```

Verify propagation:

```bash
dig shipflow.example.com +short
```

With a 300s TTL (pre-cutover setting), propagation takes at most 5 minutes.

## Alembic Migration Rollback

If the deployment included a database migration that needs reverting:

### Roll back one migration

```bash
kubectl exec -it deployment/backend -n shipflow -- alembic downgrade -1
```

### Roll back to a specific revision

```bash
# Check current migration state
kubectl exec -it deployment/backend -n shipflow -- alembic current

# Check migration history
kubectl exec -it deployment/backend -n shipflow -- alembic history --verbose

# Downgrade to a specific revision
kubectl exec -it deployment/backend -n shipflow -- alembic downgrade <revision_id>
```

### Important considerations

- **Data loss risk**: Downgrading migrations may drop columns or tables. Review the migration's `downgrade()` function before running.
- **Order matters**: Roll back the migration *before* rolling back the deployment if the old code can't work with the new schema.
- **If downgrade is destructive**: Consider whether it's safer to deploy a forward fix instead.

## Post-Rollback Verification

Run these checks after any rollback:

### 1. Health and readiness

```bash
curl -s https://shipflow.example.com/health | jq .
# Expected: {"status":"ok"}

curl -s https://shipflow.example.com/ready | jq .
# Expected: {"status":"ready","checks":{"database":"ok","redis":"ok","queue":"ok"}}
```

### 2. Pod status

```bash
kubectl get pods -n shipflow
# All pods should be Running with 0 restarts
```

### 3. Smoke tests

```bash
# Login
curl -sf -X POST https://shipflow.example.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@shipflow.ai","password":"<password>"}'

# List vessels (with token)
curl -sf https://shipflow.example.com/api/v1/vessels \
  -H "Authorization: Bearer <token>"
```

### 4. Check error rate in Grafana

Open the **HTTP Overview** dashboard and verify:
- 5xx error rate has dropped to normal (< 1%)
- P95 latency is back to normal (< 500ms)

### 5. Check queue processing

```bash
# Verify workers are processing
kubectl logs -l app.kubernetes.io/component=worker -n shipflow --tail=20

# Verify queue depth is stable or decreasing
kubectl exec -it deployment/backend -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('Queue depth:', r.llen('shipflow:parse_jobs'))
"
```

## Notify Stakeholders

Post in Slack `#shipflow-ops`:

> **Rollback completed** — deployment/backend reverted to revision N.
> - Reason: [brief description]
> - Health: all systems green
> - Next steps: investigating root cause, fix expected in [timeframe]

## Post-Rollback

1. Create a post-incident review ticket
2. Identify root cause of the failed deployment
3. Add regression test if applicable
4. Re-deploy with fix through the normal CI/CD pipeline
