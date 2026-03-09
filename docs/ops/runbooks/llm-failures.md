# Runbook: LLM / AI Parse Failures

## Alerts

- **AIParseSlowness** — `ai_parse_duration_seconds` P95 exceeds 30 seconds
- **AIParseFailureRate** — `rate(ai_parse_total{status="error"}[5m])` exceeds threshold
- **CircuitBreakerOpen** — `circuit_breaker_state{name="llm"} == 1`

## Symptoms

- AI email parse jobs failing or taking excessively long
- Users see "processing" status that never resolves to "completed"
- Circuit breaker tripped — all new parse requests rejected immediately
- Workers logging `CircuitBreakerOpen` exceptions

## Diagnosis

### 1. Check AI Parse Metrics in Grafana

```promql
# Parse success vs error rate
sum by (status) (rate(ai_parse_total[5m]))

# Parse duration P95
histogram_quantile(0.95, rate(ai_parse_duration_seconds_bucket[5m]))

# Circuit breaker state (0=closed, 1=open, 2=half_open)
circuit_breaker_state{name="llm"}

# Circuit breaker trip count
rate(circuit_breaker_trips_total{name="llm"}[1h])
```

### 2. Check OpenAI Status Page

Visit [status.openai.com](https://status.openai.com) for ongoing incidents.

If OpenAI reports degradation or an outage, the circuit breaker response is expected behavior — no action needed beyond monitoring.

### 3. Check Worker Logs

```
{namespace="shipflow", container="worker"} | json | message=~".*LLM.*|.*OpenAI.*|.*circuit.*|.*parse.*failed.*"
```

Common error patterns:

| Log message | Meaning |
|-------------|---------|
| `CircuitBreakerOpen: Circuit breaker 'llm' is open` | Too many consecutive failures, breaker tripped |
| `Transient error on email ... retrying in Ns` | Retryable error, backoff in progress |
| `Failed to process email ... after N attempts` | All retries exhausted, email marked as `failed` |
| `TimeoutError` | LLM call exceeded `LLM_TIMEOUT_SECONDS` (60s) |
| `RateLimitError` or `429` | OpenAI rate limit hit |
| `AuthenticationError` or `401` | API key invalid or expired |

### 4. Check LLM API Key Validity

```bash
kubectl exec -it deployment/worker -n shipflow -- python -c "
import httpx, os
r = httpx.get(
    os.environ.get('LLM_API_URL', 'https://api.openai.com/v1') + '/models',
    headers={'Authorization': f\"Bearer {os.environ['LLM_API_KEY']}\"},
    timeout=10
)
print(f'Status: {r.status_code}')
if r.status_code != 200:
    print(f'Error: {r.text[:500]}')
else:
    print('API key is valid')
"
```

### 5. Check Circuit Breaker Configuration

Current settings (from `app/config.py`):

| Setting | Value | Meaning |
|---------|-------|---------|
| `CB_FAILURE_THRESHOLD` | 5 | Trips open after 5 consecutive failures |
| `CB_RECOVERY_TIMEOUT` | 30s | Waits 30s before probing (half-open) |
| `CB_HALF_OPEN_MAX_CALLS` | 3 | Allows 3 probe requests in half-open state |

The circuit breaker auto-recovers: after 30 seconds in the `open` state, it transitions to `half_open` and allows 3 probe requests. A single success resets it to `closed`.

## Mitigation

### If OpenAI outage — wait and monitor

The circuit breaker will automatically recover once OpenAI is back. No manual action needed.

1. Monitor `circuit_breaker_state{name="llm"}` in Grafana
2. Once it returns to `0` (closed), check that queued jobs start processing
3. If the queue grew large during the outage, consider scaling workers temporarily:

```bash
kubectl scale deployment/worker -n shipflow --replicas=5
```

### If API key issue — rotate key

1. Generate a new API key from the OpenAI dashboard
2. Update the K8s secret:

```bash
# Encode the new key
echo -n "sk-new-key-here" | base64

# Edit the secret
kubectl edit secret shipflow-secrets -n shipflow
# Update the LLM_API_KEY field with the new base64 value
```

3. Restart worker pods to pick up the new key:

```bash
kubectl rollout restart deployment/worker -n shipflow
kubectl rollout restart deployment/backend -n shipflow
```

### If timeout issues — increase timeout temporarily

```bash
kubectl edit configmap shipflow-config -n shipflow
# Change LLM_TIMEOUT_SECONDS from "60" to "90"
```

Then restart workers:

```bash
kubectl rollout restart deployment/worker -n shipflow
```

Revert after the provider stabilizes.

### If rate limiting — reduce concurrency

If OpenAI is rate-limiting requests:

1. Reduce worker replicas to lower concurrent LLM calls:

```bash
kubectl scale deployment/worker -n shipflow --replicas=1
```

2. Jobs will process more slowly but won't trigger rate limits
3. Scale back up once rate limits are no longer an issue

### Reprocess failed emails

After the underlying issue is resolved, failed emails can be resubmitted:

```bash
kubectl exec -it deployment/backend -n shipflow -- python -c "
import asyncio
from sqlalchemy import text
from app.database import engine

async def check_failed():
    async with engine.connect() as conn:
        result = await conn.execute(text(\"\"\"
            SELECT id, subject, processing_status, error_reason, updated_at
            FROM emails
            WHERE processing_status = 'failed'
            ORDER BY updated_at DESC
            LIMIT 20
        \"\"\"))
        for row in result:
            print(dict(row._mapping))

asyncio.run(check_failed())
"
```

Resubmit via the API: `PUT /api/v1/ai/emails/{id}/status` to reset status, then `POST /api/v1/ai/parse` to re-enqueue.

## Escalation

- **Prolonged OpenAI outage (> 1 hour)**: Communicate to users that AI parsing is temporarily degraded. Update the status page. Users can still manually create port calls and DAs.
- **API key compromised**: Rotate immediately, notify security team.
- If not resolved in 15 minutes: Page engineering lead.
