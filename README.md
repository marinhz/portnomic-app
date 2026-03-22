# Portnomic

Multi-tenant maritime agency SaaS platform with AI-powered email parsing, disbursement account generation, and comprehensive vessel/port call management.

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Alembic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS v4, React Router v7, Axios
- **Infrastructure**: Docker Compose (PostgreSQL 16 + Redis 7)

## Quick Start

### 1. Start infrastructure

```bash
docker compose up -d
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e ".[dev]"
```

### 3. Run database migrations

```bash
cd backend
alembic upgrade head
```

### 4. Seed demo data

```bash
cd backend
python -m app.seed
```

This creates:
- **Tenant**: Portnomic Demo
- **Admin user**: `admin@portnomic.ai` / `admin123`
- **Roles**: Admin (full access), Operator (vessel + port call access)
- **Sample ports**: Rotterdam, Singapore, Shanghai, Hamburg, Piraeus

### 5. Start the backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 5b. Start the AI parse worker (optional)

```bash
cd backend
arq app.worker.WorkerSettings
```

The worker processes AI parse jobs from the Redis queue. It also polls IMAP if configured in `.env`.

### 6. Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: http://localhost:5173

## All-in-one container (easy deploy & develop)

For development or small deployments (staging, demo, single VM), use the all-in-one container that runs API, ARQ worker, and frontend in a single process group.

### Development (with postgres + redis)

```bash
# Copy .env.example to .env and configure
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

- **Migrations** run automatically on container startup (`alembic upgrade head`)
- **Frontend:** http://localhost
- **API:** http://localhost/api
- **Docs:** http://localhost/docs (when ENVIRONMENT=development)

### Simple production

```bash
# Set POSTGRES_PASSWORD and other vars in .env
docker compose -f docker-compose.prod-simple.yml up -d
```

### When to use all-in-one vs multi-service

| Use case | Compose file | Notes |
|----------|--------------|-------|
| Local dev (all-in-one) | `docker-compose.yml` + `docker-compose.dev.yml` | One command, full stack |
| Staging / demo / single VM | `docker-compose.prod-simple.yml` | One app container |
| Production (scaling) | `docker-compose.prod.yml` | Separate backend, worker, frontend; HPA-ready |

**Required env vars** (same as multi-service): `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `MFA_ENCRYPTION_KEY`. For OAuth: `OAUTH_REDIRECT_BASE_URL`, `OAUTH_FRONTEND_SUCCESS_URL` (e.g. `http://your-domain/api`, `http://your-domain/settings/integrations`).

### Deploy on VPS with Traefik (app.portnomic.com)

If Traefik is already running (e.g. for portnomic.com), use the standalone Traefik compose (no port 80 conflict):

```bash
docker compose -f docker-compose.traefik.yml up -d
```

See **[docs/deploy-vps-traefik.md](docs/deploy-vps-traefik.md)** for the full deployment guide (clone, `.env`, migrations, troubleshooting).

---

## Project Structure

```
shipflow/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app, middleware, exception handlers
│   │   ├── config.py            # Settings (pydantic-settings)
│   │   ├── database.py          # Async SQLAlchemy engine
│   │   ├── redis_client.py      # Redis connection
│   │   ├── seed.py              # Development seed data
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── dependencies/        # FastAPI deps (auth, tenant, RBAC)
│   │   ├── services/            # Business logic layer
│   │   └── routers/             # API route handlers
│   ├── alembic/                 # Database migrations
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── api/                 # HTTP client + TypeScript types
│   │   ├── auth/                # Auth context, login, protected routes
│   │   ├── layout/              # App shell, sidebar navigation
│   │   ├── pages/               # Dashboard, vessels, port calls, admin
│   │   ├── components/          # Reusable UI components
│   │   └── router.tsx           # Route definitions
│   └── package.json
├── docker/
│   ├── Dockerfile.all-in-one   # All-in-one image (API + worker + frontend)
│   ├── supervisord.conf
│   └── nginx-all-in-one.conf
├── docker-compose.yml
├── docker-compose.dev.yml      # Dev with all-in-one app
├── docker-compose.prod.yml     # Multi-service production
├── docker-compose.prod-simple.yml  # Simple prod (all-in-one)
└── .env
```

## API Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | /api/v1/auth/login | Login | None |
| POST | /api/v1/auth/mfa | MFA verification | MFA token |
| POST | /api/v1/auth/refresh | Refresh access token | Refresh token |
| GET | /api/v1/auth/me | Current user info | JWT |
| GET/POST | /api/v1/vessels | List/create vessels | JWT + vessel:read/write |
| GET/PUT | /api/v1/vessels/{id} | Get/update vessel | JWT + vessel:read/write |
| GET/POST | /api/v1/ports | List/create ports | JWT + port_call:read/write |
| GET/POST | /api/v1/port-calls | List/create port calls | JWT + port_call:read/write |
| GET/PUT | /api/v1/port-calls/{id} | Get/update port call | JWT + port_call:read/write |
| GET | /api/v1/emails | List emails (tenant) | JWT + ai:parse |
| GET | /api/v1/emails/{id} | Get email detail | JWT + ai:parse |
| POST | /api/v1/ai/parse | Submit email for AI parsing | JWT + ai:parse |
| GET | /api/v1/ai/parse/{job_id} | Get parse job status/result | JWT + ai:parse |
| PUT | /api/v1/ai/emails/{id}/status | Manual override email status | JWT + ai:parse |
| POST | /webhooks/inbound-email | Webhook for inbound emails | Webhook signature |
| GET/POST | /api/v1/admin/users | List/create users | JWT + admin:users |
| GET/PUT | /api/v1/admin/users/{id} | Get/update user | JWT + admin:users |
| GET/POST | /api/v1/admin/roles | List/create roles | JWT + admin:roles |
| GET | /api/v1/integrations/email | List mail connections | JWT + admin:users |
| GET | /api/v1/integrations/email/connect | Start OAuth flow (Gmail/Outlook) | JWT + admin:users |
| GET | /api/v1/integrations/email/callback | OAuth callback | State token |
| DELETE | /api/v1/integrations/email/{id} | Disconnect mailbox | JWT + admin:users |
| POST | /api/v1/integrations/email/imap | Add IMAP connection | JWT + admin:users |
| GET | /health | Health check | None |

## Security

- JWT access tokens (15 min) + refresh tokens (7 days)
- MFA (TOTP) support with encrypted secrets
- RBAC with tenant-scoped permissions
- Strict multi-tenant isolation on all queries
- Append-only audit logging
- Rate limiting per IP
- CORS restricted to frontend origin
- Pydantic input validation on all endpoints
