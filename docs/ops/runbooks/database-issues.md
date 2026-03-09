# Runbook: Database Issues

## Alerts

- **DatabaseDown** — `/ready` endpoint reports `database: "unavailable"`
- **HighDBLatency** — `db_query_duration_seconds` P95 exceeds 1 second for 5 minutes

## Symptoms

- API returning 503 on `/ready` with `"database": "unavailable"`
- Slow page loads across the entire application
- Connection timeout errors in backend logs
- Users unable to log in, view data, or create records

## Diagnosis

### 1. Check RDS Console

Navigate to **AWS Console → RDS → shipflow production instance**. Check:

- **CPU utilization** — sustained > 80% indicates query or load issue
- **Database connections** — approaching `max_connections` (default: ~400 for db.t3.medium)
- **Read IOPS / Write IOPS** — spikes may indicate heavy queries or vacuum activity
- **Freeable memory** — low memory causes swapping and degraded performance

### 2. Check Grafana DB Metrics

- `db_query_duration_seconds` — histogram of query latency by operation
- `http_request_duration_seconds{endpoint=~"/api/v1/.*"}` — if all endpoints are slow, DB is likely the bottleneck

### 3. Check Connection Pool

The backend uses SQLAlchemy async with `pool_size=20, max_overflow=10` (total max: 30 connections per pod). With 3 backend pods, that's up to 90 connections.

```bash
# Check active connections on RDS
kubectl exec -it deployment/backend -n shipflow -- python -c "
from sqlalchemy import text
import asyncio
from app.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(\"\"\"
            SELECT count(*) as total,
                   count(*) FILTER (WHERE state = 'active') as active,
                   count(*) FILTER (WHERE state = 'idle') as idle,
                   count(*) FILTER (WHERE wait_event_type = 'Lock') as waiting
            FROM pg_stat_activity
            WHERE datname = 'shipflow'
        \"\"\"))
        print(dict(result.fetchone()._mapping))

asyncio.run(check())
"
```

### 4. Check for Long-Running Transactions

```bash
kubectl exec -it deployment/backend -n shipflow -- python -c "
from sqlalchemy import text
import asyncio
from app.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text(\"\"\"
            SELECT pid, now() - pg_stat_activity.query_start AS duration,
                   query, state
            FROM pg_stat_activity
            WHERE (now() - pg_stat_activity.query_start) > interval '30 seconds'
              AND state != 'idle'
              AND datname = 'shipflow'
            ORDER BY duration DESC
            LIMIT 10
        \"\"\"))
        for row in result:
            print(dict(row._mapping))

asyncio.run(check())
"
```

### 5. Check Loki for DB Errors

```
{namespace="shipflow", container="backend"} | json | message=~".*connection.*|.*timeout.*|.*deadlock.*"
```

## Mitigation

### Kill long-running queries

```bash
kubectl exec -it deployment/backend -n shipflow -- python -c "
from sqlalchemy import text
import asyncio
from app.database import engine

async def kill(pid):
    async with engine.connect() as conn:
        await conn.execute(text(f'SELECT pg_terminate_backend({pid})'))
        await conn.commit()
        print(f'Terminated PID {pid}')

asyncio.run(kill(<PID>))
"
```

Replace `<PID>` with the process ID from the long-running query check above.

### Restart backend pods to reset connection pool

If the connection pool is exhausted or connections are stale:

```bash
kubectl rollout restart deployment/backend -n shipflow
kubectl rollout restart deployment/worker -n shipflow
```

This forces new connections to be established. The PDB ensures at least 1 pod stays available.

### Increase pool size (temporary)

If connection exhaustion is the issue and query volume is legitimate, update the ConfigMap:

```bash
kubectl edit configmap shipflow-config -n shipflow
# Add: DB_POOL_TIMEOUT=60
```

Then restart pods. For a permanent change, update `k8s/base/configmap.yaml`.

### Failover to read replica

If the primary is degraded but the read replica is healthy, backend read-only queries can be routed to the replica. This requires a code change to use a separate `DATABASE_URL_READ` connection.

### Emergency: RDS failover

If the primary is unresponsive:

```bash
aws rds reboot-db-instance --db-instance-identifier shipflow-prod --force-failover
```

This promotes the standby (Multi-AZ). Expect 1–2 minutes of downtime.

## Escalation

- If RDS metrics show infrastructure-level issues (disk, CPU, memory) — open AWS support case with severity "Production system impaired"
- If data corruption is suspected — page the DB admin and engineering manager immediately
- If not resolved in 15 minutes — page the engineering lead
