# Runbook: Queue Backlog

## Alerts

- **QueueBacklog** — `queue_depth{queue_name="shipflow:parse_jobs"} > 50` for 10 minutes
- **QueueBacklogCritical** — `queue_depth{queue_name="shipflow:parse_jobs"} > 100` for 5 minutes

## Symptoms

- AI parse jobs not completing — users see "processing" status indefinitely
- `processing_status` stuck at `"queued"` or `"pending"` in the database
- Queue depth metric rising in Grafana
- Workers appear idle or are crash-looping

## Diagnosis

### 1. Check Queue Depth in Grafana

Open the **Queue Health** dashboard. Look at `queue_depth{queue_name="shipflow:parse_jobs"}`.

Alternatively, query Redis directly:

```bash
kubectl exec -it deployment/backend -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('Queue depth:', r.llen('shipflow:parse_jobs'))
"
```

### 2. Check Worker Pod Status

```bash
kubectl get pods -n shipflow -l app.kubernetes.io/component=worker
```

Look for:
- **0/1 Running** or **CrashLoopBackOff** — workers are failing to start
- **Restarts > 0** — workers are crashing during processing
- **Pending** — not enough cluster resources to schedule worker pods

### 3. Check Worker Logs

```bash
kubectl logs -l app.kubernetes.io/component=worker -n shipflow --tail=200
```

Or via Loki:

```
{namespace="shipflow", container="worker"} | json | level=~"ERROR|WARNING"
```

Common errors:
- `CircuitBreakerOpen` — LLM client circuit breaker tripped (see [llm-failures.md](llm-failures.md))
- `ConnectionRefusedError` — Redis or DB unreachable
- `TimeoutError` — LLM call timed out (current timeout: 60s)
- `Max retries exceeded` — transient errors exhausted all 3 retry attempts

### 4. Check Redis Connectivity

```bash
kubectl exec -it deployment/worker -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
print('PING:', r.ping())
print('INFO clients:', r.info('clients')['connected_clients'])
"
```

### 5. Check HPA Status

```bash
kubectl get hpa worker-hpa -n shipflow
kubectl describe hpa worker-hpa -n shipflow
```

Check if the HPA is at max replicas or unable to scale due to resource constraints.

## Mitigation

### Scale workers manually

```bash
# Scale to 5 replicas (max allowed by HPA: 8)
kubectl scale deployment/worker -n shipflow --replicas=5

# Verify
kubectl get pods -n shipflow -l app.kubernetes.io/component=worker
```

### Restart stuck workers

If workers appear healthy but not processing:

```bash
kubectl rollout restart deployment/worker -n shipflow
kubectl rollout status deployment/worker -n shipflow
```

### Check LLM availability

If worker logs show `CircuitBreakerOpen` or LLM timeouts:

1. Check the circuit breaker state in Grafana: `circuit_breaker_state{name="llm"}`
   - 0 = closed (healthy)
   - 1 = open (rejecting calls)
   - 2 = half_open (probing)

2. If the breaker is open, the LLM provider may be down. Check [status.openai.com](https://status.openai.com). See [llm-failures.md](llm-failures.md).

3. The circuit breaker auto-recovers after 30 seconds — if the LLM is back, workers will resume.

### Drain corrupted jobs

If specific jobs are causing repeated failures and blocking the queue:

```bash
# Inspect the next job in queue without removing it
kubectl exec -it deployment/backend -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
jobs = r.lrange('shipflow:parse_jobs', 0, 4)
for j in jobs:
    print(j.decode())
"

# Remove a specific stuck job (move to dead letter manually)
kubectl exec -it deployment/backend -n shipflow -- python -c "
import redis, os
r = redis.from_url(os.environ['REDIS_URL'])
removed = r.lrem('shipflow:parse_jobs', 1, '<job_payload>')
print('Removed:', removed)
"
```

## Escalation

- If workers cannot process due to LLM provider outage, communicate delay to users via the status page or Slack.
- If Redis itself is unreachable, escalate to DevOps / AWS support (ElastiCache issue).
- If not resolved in 15 minutes, page the engineering lead.
