# Backend Agent — ShipFlow AI

Use with **fastapi-python** and **python-project-structure**. Applies to FastAPI app, auth, services, repositories, and DB.

## Structure

- One FastAPI app; domain modules: `auth`, `vessels`, `port_calls`, `da`, `ai`, `admin`.
- Tenant and RBAC via dependencies; services assume `tenant_id` and `current_user` are set.
- Long-running work (AI parse, PDF, email) → background workers; API enqueues and returns job id or 202.

## Key Components

| Component | Responsibility |
|-----------|----------------|
| Auth service | Login, MFA challenge, JWT issue/validate/refresh (PyJWT, MFA lib) |
| Tenant middleware | Resolve tenant from JWT; inject into request context (dependency) |
| RBAC middleware | Check permission for (user, resource, action) before handler |
| Vessel / Port call / DA services | CRUD and business logic; all queries filtered by `tenant_id` |
| Email ingest | Receive email (IMAP/webhook), persist, enqueue for AI |
| AI orchestration | Request AI parse (internal client to AI/worker), map result to domain |
| DA service | Create/update Proforma and Final DA; run formula engine; approve/send workflow |
| PDF / notification | Trigger background job for PDF generation and email dispatch |
| Admin service | User/role CRUD (tenant-scoped) |
| Audit logger | Append-only audit events (who, what, when, resource_type, resource_id) |

## Data & Persistence

- **PostgreSQL:** All tenant-scoped tables have `tenant_id`. Composite indexes `(tenant_id, <lookup>)`.
- **Migrations:** Alembic; no destructive changes without explicit flow.
- **Redis:** Session, idempotency keys; optional cache-aside for ports/tariffs keyed by `tenant_id`.

## API Contract (Summary)

- Auth: `POST /auth/login`, `POST /auth/mfa`, `POST /auth/refresh`.
- Vessels: `GET/POST /vessels`, `GET/PUT /vessels/{id}`.
- Port calls: `GET/POST /port-calls`, `GET/PUT /port-calls/{id}`.
- DA: `POST /da/generate`, `GET /da/{id}`, `POST /da/{id}/approve`, `POST /da/{id}/send`.
- AI: `POST /ai/parse`, `GET /ai/parse/{job_id}`.
- Admin: `GET/POST /admin/users`, `GET /admin/roles`.

All except login/MFA/refresh require JWT + tenant resolution + permission check.

## Conventions

- Pydantic for all request/response and validation.
- HTTPException for expected errors; consistent error envelope.
- Timeouts and retries on DB, Redis, and external calls.
- No secrets or PII in logs; use request_id and correlation_id for tracing.
