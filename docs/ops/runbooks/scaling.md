# Runbook: Scaling

## HPA Status

Check current autoscaling state:

```bash
kubectl get hpa -n shipflow
kubectl describe hpa backend-hpa -n shipflow
kubectl describe hpa worker-hpa -n shipflow
```

### Current HPA Configuration

| Deployment | Min | Max | CPU Target | Scale Up | Scale Down |
|-----------|-----|-----|-----------|----------|------------|
| Backend | 2 | 10 | 70% avg | +3 pods/60s | -1 pod/300s |
| Worker | 2 | 8 | 70% avg | +2 pods/60s | -1 pod/300s |

Backend also scales on memory (80% avg utilization).

## Manual Scaling

### Backend API

```bash
# Scale to N replicas
kubectl scale deployment/backend -n shipflow --replicas=N

# Example: scale up for expected high traffic
kubectl scale deployment/backend -n shipflow --replicas=6

# Verify
kubectl get pods -n shipflow -l app.kubernetes.io/component=api
```

**Note:** Manual scaling overrides HPA temporarily. The HPA will adjust replicas back to its calculated target within its stabilization window (scale-down: 300s). To keep manual scaling in effect, either update the HPA `minReplicas` or disable HPA temporarily.

### Workers (Queue Backlog)

When the parse queue is growing faster than workers can process:

```bash
# Check current queue depth
kubectl exec -it deployment/backend -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('Queue depth:', r.llen('shipflow:parse_jobs'))
"

# Scale workers
kubectl scale deployment/worker -n shipflow --replicas=5

# Monitor queue draining
watch -n 10 "kubectl exec deployment/backend -n shipflow -- python -c \"
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('Queue depth:', r.llen('shipflow:parse_jobs'))
\""
```

Scale workers back down after the backlog clears:

```bash
kubectl scale deployment/worker -n shipflow --replicas=2
```

### Frontend

The frontend serves static assets via Nginx and is lightweight. Scaling is rarely needed:

```bash
kubectl scale deployment/frontend -n shipflow --replicas=3
```

## Update HPA Limits

To permanently change scaling bounds:

### Temporarily via kubectl

```bash
# Increase backend max replicas
kubectl patch hpa backend-hpa -n shipflow --type=merge \
  -p '{"spec":{"maxReplicas":15}}'

# Increase worker min replicas (during high-load period)
kubectl patch hpa worker-hpa -n shipflow --type=merge \
  -p '{"spec":{"minReplicas":4}}'
```

### Permanently via kustomize

Edit `k8s/overlays/production/kustomization.yaml` and add a patch for the HPA, then apply:

```bash
kubectl apply -k k8s/overlays/production
```

## Cost Awareness

| Component | Requests (per pod) | Limits (per pod) | Max pods | Max cluster cost contribution |
|-----------|-------------------|-------------------|----------|-------------------------------|
| Backend | 500m CPU, 512Mi mem | 1 CPU, 1Gi mem | 10 | 10 vCPU, 10Gi mem |
| Worker | 500m CPU, 512Mi mem | 1 CPU, 1Gi mem | 8 | 8 vCPU, 8Gi mem |
| Frontend | 50m CPU, 64Mi mem | 100m CPU, 128Mi mem | 2 | 0.2 vCPU, 256Mi mem |

Before scaling beyond current HPA limits, verify:
1. EKS node group has capacity (check **AWS Console → EKS → Node Groups**)
2. Cluster Autoscaler is enabled and configured for the node group
3. Budget approval for sustained scaling (each additional node costs ~$X/month)

## Database Scaling (RDS)

RDS instance class changes require a maintenance window or immediate apply (with brief downtime for single-AZ).

### Check current instance

```bash
aws rds describe-db-instances --db-instance-identifier shipflow-prod \
  --query "DBInstances[0].{Class:DBInstanceClass,CPU:ProcessorFeatures,Storage:AllocatedStorage,MultiAZ:MultiAZEnabled,Status:DBInstanceStatus}"
```

### Scale up procedure

1. Identify the target instance class (e.g., `db.t3.medium` → `db.r6g.large`)
2. Schedule during low-traffic window if possible
3. Apply the change:

```bash
aws rds modify-db-instance \
  --db-instance-identifier shipflow-prod \
  --db-instance-class db.r6g.large \
  --apply-immediately
```

4. Monitor the modification status:

```bash
aws rds describe-db-instances --db-instance-identifier shipflow-prod \
  --query "DBInstances[0].DBInstanceStatus"
```

5. After modification completes, verify application connectivity:

```bash
curl -s https://shipflow.example.com/ready | jq .checks.database
```

### Storage scaling

RDS storage can be increased (never decreased) without downtime:

```bash
aws rds modify-db-instance \
  --db-instance-identifier shipflow-prod \
  --allocated-storage 100 \
  --apply-immediately
```

## Redis Scaling (ElastiCache)

For ElastiCache Redis, scaling options depend on the cluster mode:

- **Vertical scaling** (node type change): requires a new replication group or maintenance window
- **Read replicas**: add replicas for read-heavy workloads

```bash
aws elasticache describe-cache-clusters --cache-cluster-id shipflow-prod-redis
```

Consult AWS documentation for the specific scaling operation needed. Redis scaling may cause brief connectivity interruptions — coordinate with the team and monitor the `/ready` endpoint.
