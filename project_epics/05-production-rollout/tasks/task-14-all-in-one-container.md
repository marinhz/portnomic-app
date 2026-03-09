# Task 5.14 — All-in-one container (easy deploy & develop)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Provide an all-in-one container that runs backend API, ARQ workers, and frontend in a single process group, so developers and small deployments can run the full stack with one command instead of managing separate backend, worker, and frontend services.

---

## Problem statement

- **Current setup:** `docker-compose.prod.yml` requires 4 application services: `backend`, `worker`, `frontend`, plus `postgres` and `redis`.
- **Pain:** Developers must run backend, worker, and frontend separately; local dev requires multiple terminals or complex orchestration.
- **Deploy pain:** Small deployments (e.g. single VM, staging, demo) must manage multiple containers and networking.
- **Goal:** One container that runs API + workers + static frontend; one `docker run` or `docker compose up` for the app layer.

---

## Scope

### 1. All-in-one image

- **Single Dockerfile** (e.g. `Dockerfile.all-in-one` or `docker/Dockerfile`) that:
  - Builds frontend (Node → static assets).
  - Builds backend (Python + uvicorn + arq).
  - Copies both into a runtime image.
- **Process manager:** Use `supervisord` (or `s6-overlay` / `tini` + shell) to run:
  - `uvicorn app.main:app --host 0.0.0.0 --port 8000` (API)
  - `arq app.worker.WorkerSettings` (ARQ worker)
  - `nginx` (serve frontend static files + proxy `/api` to backend)
- **Single exposed port:** e.g. 80 (nginx) or 8000 (if nginx proxies to backend and serves static from same port).
- **Healthcheck:** Hit `/health` on the API (via nginx proxy or direct) to verify both API and nginx are up.

### 2. Nginx configuration

- Serve frontend from `/` (or `/app`).
- Proxy `/api`, `/docs`, `/openapi.json`, `/health` to `http://127.0.0.1:8000`.
- Ensure SPA routing: fallback unknown paths to `index.html`.

### 3. Development mode

- **docker-compose.dev.yml** (or extend `docker-compose.yml`):
  - `app` service: all-in-one image.
  - `postgres`, `redis` as before.
  - Single command: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up` (or equivalent) runs full stack.
- **Optional:** Volume mounts for backend/frontend hot reload in dev (e.g. mount `backend/app` and run uvicorn with `--reload`; mount frontend dist or use dev server). If hot reload adds complexity, document that dev uses the built image for simplicity.

### 4. Production / deploy

- **docker-compose.prod-simple.yml** (or profile): One `app` service + postgres + redis. No separate backend/worker/frontend services.
- **Environment:** Same env vars as current setup (DB, Redis, secrets). Document required vars.
- **Resource limits:** Single container may need higher memory (e.g. 1G) since it runs API + worker + nginx.

### 5. Backward compatibility

- Keep existing `backend/Dockerfile`, `frontend/Dockerfile`, and `docker-compose.prod.yml` for production deployments that prefer separate services (scaling, HPA). The all-in-one option is additive.

---

## Acceptance criteria

- [ ] All-in-one Dockerfile builds successfully and runs API, worker, and frontend.
- [ ] Single `docker compose up` (dev profile) starts postgres, redis, and the all-in-one app; frontend is reachable at `http://localhost` and API at `http://localhost/api` (or documented path).
- [ ] ARQ worker processes jobs from Redis; parse/ingest jobs complete.
- [ ] Healthcheck passes; container is usable in production-like environments.
- [ ] README or CONTRIBUTING documents: how to run all-in-one for dev, required env vars, and when to use all-in-one vs. multi-service.

---

## Implementation notes

### Suggested layout

```
docker/
  Dockerfile.all-in-one    # Multi-stage: frontend build, backend build, runtime with supervisord
  supervisord.conf         # Programs: uvicorn, arq, nginx
  nginx-all-in-one.conf    # Serve static + proxy /api to backend
```

### Supervisor example

```ini
[supervisord]
nodaemon=true

[program:uvicorn]
command=uvicorn app.main:app --host 127.0.0.1 --port 8000
directory=/app
autorestart=true

[program:arq]
command=arq app.worker.WorkerSettings
directory=/app
autorestart=true

[program:nginx]
command=nginx -g "daemon off;"
autorestart=true
```

### Nginx proxy

- `location /api` → `proxy_pass http://127.0.0.1:8000`
- `location /` → serve `/usr/share/nginx/html` (frontend build)
- `location /health` → proxy to backend for liveness

### Env vars

- Reuse existing: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, etc. No new vars required.

---

## Related code

- `backend/Dockerfile` — backend build
- `frontend/Dockerfile` — frontend build
- `docker-compose.yml` — dev (postgres, redis only)
- `docker-compose.prod.yml` — current multi-service prod
- `backend/app/worker.py` — ARQ WorkerSettings
- `frontend/nginx.conf` — current frontend nginx config (reference for SPA routing)

---

## Dependencies

- None (uses existing backend, frontend, worker).

---

## Out of scope (for now)

- Kubernetes all-in-one Deployment (can be added later; same image).
- Hot reload in container (optional follow-up).
- Scaling workers independently (use multi-service compose for that).
