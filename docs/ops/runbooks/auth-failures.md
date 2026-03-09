# Runbook: Auth Failures

## Alerts

- **HighLoginFailureRate** — `rate(auth_login_failures_total[5m])` exceeds threshold
- **PermissionDeniedSpike** — `rate(permission_denied_total[5m])` exceeds threshold

## Symptoms

- Users reporting "Invalid credentials" or "Permission denied"
- Spike in login failure metrics
- 401/403 responses across multiple endpoints
- Potential brute-force attack pattern

## Diagnosis

### 1. Check Login Failure Metrics

In Grafana, query:

```promql
# Failure rate by reason
sum by (reason) (rate(auth_login_failures_total[5m]))

# Failure reasons: "invalid_credentials", "account_locked", "tenant_inactive", "mfa_required", "mfa_invalid"
```

Look for patterns:
- **Single reason dominating** — likely a systemic issue (e.g., JWT secret mismatch)
- **Many different `user_email_hash` values, same reason** — likely a configuration issue affecting all users
- **One `user_email_hash` with many failures** — likely a brute-force attempt on a single account

### 2. Check Permission Denied Metrics

```promql
# Permission denied by endpoint
sum by (endpoint) (rate(permission_denied_total[5m]))
```

If a specific endpoint is spiking, it may indicate a role/permission misconfiguration after a deployment.

### 3. Check Logs

```
{namespace="shipflow", container="backend"} | json | level="WARNING" | message=~".*login.*failed.*|.*permission.*denied.*"
```

### 4. Verify JWT Secret Consistency

If all users are failing to authenticate (not just login, but also existing sessions):

```bash
# Check that all backend pods have the same JWT_SECRET
kubectl get pods -n shipflow -l app.kubernetes.io/component=api -o name | while read pod; do
  echo "--- $pod ---"
  kubectl exec $pod -n shipflow -- printenv JWT_SECRET | md5sum
done
```

All pods must show the same hash. If they differ, the secret was updated but not all pods restarted.

### 5. Verify MFA Encryption Key

If MFA verification is failing for all users:

```bash
# Same check for MFA_ENCRYPTION_KEY
kubectl get pods -n shipflow -l app.kubernetes.io/component=api -o name | while read pod; do
  echo "--- $pod ---"
  kubectl exec $pod -n shipflow -- printenv MFA_ENCRYPTION_KEY | md5sum
done
```

### 6. Check Token Expiry Settings

```bash
kubectl exec -it deployment/backend -n shipflow -- printenv | grep JWT
# Expected: JWT_ACCESS_EXPIRY_MINUTES=15, JWT_REFRESH_EXPIRY_MINUTES=10080
```

## Mitigation

### If brute-force attack detected

1. Check that rate limiting is active (20 req/min on auth endpoints):

```bash
# Test rate limit
for i in $(seq 1 25); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST https://shipflow.example.com/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"wrong"}'
done
# Should see 429 after ~20 requests
```

2. If rate limiting is not catching it (distributed attack), block offending IPs at the ingress level:

```bash
kubectl annotate ingress shipflow-ingress -n shipflow \
  nginx.ingress.kubernetes.io/server-snippet="deny <IP_ADDRESS>;"
```

3. Consider temporarily lowering `RATE_LIMIT_AUTH_PER_MINUTE` in the ConfigMap.

### If JWT secret was rotated incorrectly

If the JWT secret was changed but pods weren't restarted, all existing tokens become invalid:

```bash
# Rolling restart to pick up the new secret
kubectl rollout restart deployment/backend -n shipflow
kubectl rollout status deployment/backend -n shipflow
```

Users will need to log in again (existing access tokens are invalidated).

### If MFA encryption key mismatch

If the MFA encryption key changed, existing MFA secrets cannot be decrypted:

1. Verify the key is correct in the K8s secret
2. If the key was lost, affected users will need to re-enroll MFA:
   - Admin disables MFA for affected users
   - Users re-enable MFA with new TOTP setup

### If permission misconfiguration after deployment

1. Check which roles/permissions were changed in the latest migration
2. Verify roles in the database:

```bash
kubectl exec -it deployment/backend -n shipflow -- python -c "
import asyncio
from sqlalchemy import text
from app.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text('SELECT id, name, permissions FROM roles LIMIT 20'))
        for row in result:
            print(dict(row._mapping))

asyncio.run(check())
"
```

3. If roles are wrong, fix via migration rollback or direct DB update (with audit trail)

## Escalation

- **Suspected security incident** (credential stuffing, data exfiltration attempt): Immediately notify the security team and follow incident response procedures. Do not delay.
- **All users locked out**: Page engineering lead — this is a P1 outage.
- If not resolved in 15 minutes: Page engineering lead.
