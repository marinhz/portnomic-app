# Deploy Portnomic App on VPS with Traefik

This guide walks through deploying the Portnomic app at **app.portnomic.com** on a VPS where Traefik is already running (main site at portnomic.com in `/opt/portnomic`).

## Prerequisites

- VPS with Docker and Docker Compose
- Traefik running (e.g. for portnomic.com)
- DNS: `app.portnomic.com` → your VPS IP (A record)

---

## Step 1: Create app directory on VPS

```bash
sudo mkdir -p /opt/portnomic-app
cd /opt/portnomic-app
```

---

## Step 2: Clone the repository

```bash
git clone https://github.com/marinhz/portnomic-app.git .
```

---

## Step 3: Find your Traefik network name

Traefik creates a Docker network for routing. Common names: `web`, `traefik`, `proxy`.

```bash
docker network ls | grep -E "traefik|web|proxy"
```

If your main site compose uses a network like `web` or `traefik`, note it. You'll use it in the next step.

**Edit** `docker-compose.traefik.yml` and change the network name if needed:

```yaml
networks:
  traefik:
    external: true   # Must match your Traefik network name
```

If your Traefik network is named `web`, change `traefik` to `web` in the file.

---

## Step 4: Create production `.env`

```bash
cp .env.example .env
nano .env   # or vim
```

**Required changes for production:**

| Variable | Example | Notes |
|----------|---------|-------|
| `ENVIRONMENT` | `production` | |
| `POSTGRES_PASSWORD` | Strong random password | Generate with `openssl rand -base64 32` |
| `JWT_SECRET` | Strong random string | Same as above |
| `MFA_ENCRYPTION_KEY` | Fernet key | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `CORS_ORIGINS` | `["https://app.portnomic.com"]` | Must include your app URL |
| `API_PUBLIC_BASE_URL` | `https://app.portnomic.com` | For myPOS webhooks |
| `OAUTH_REDIRECT_BASE_URL` | `https://app.portnomic.com` | For OAuth callbacks |
| `OAUTH_FRONTEND_SUCCESS_URL` | `https://app.portnomic.com/settings/integrations` | After OAuth |
| `DATABASE_URL` | `postgresql+asyncpg://shipflow:SECRET@postgres:5432/shipflow?ssl=disable` | Use `postgres` host (Docker service) |
| `DATABASE_URL_SYNC` | `postgresql://shipflow:SECRET@postgres:5432/shipflow?sslmode=disable` | Same |
| `REDIS_URL` | `redis://redis:6379/0` | Use `redis` host (Docker service) |

**Optional but recommended:**
- `LLM_API_KEY`, `LLM_API_URL`, `LLM_MODEL` – for AI parsing
- `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET` – for Gmail sync
- `SMTP_*` – for outbound email

---

## Step 5: Build and start

```bash
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml build --no-cache
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml up -d
```

---

## Step 6: Run database migrations

```bash
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml exec app alembic upgrade head
```

---

## Step 7: (Optional) Seed initial data

```bash
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml exec app python -m app.seed
```

---

## Step 8: Verify Traefik routing

1. Check Traefik sees the service:
   ```bash
   docker logs traefik 2>&1 | tail -20
   ```

2. Visit **https://app.portnomic.com** – you should see the login page.

3. If you get 404 or connection refused:
   - Ensure `app.portnomic.com` DNS points to your VPS
   - Ensure the app container is on the same network as Traefik
   - Check Traefik cert resolver name (e.g. `letsencrypt`) – edit `docker-compose.traefik.yml` if your resolver has a different name

---

## Traefik configuration notes

**Entrypoint:** The config uses `websecure` (HTTPS). If your Traefik uses `https` instead, change:
```yaml
- "traefik.http.routers.portnomic-app.entrypoints=websecure"
```
to:
```yaml
- "traefik.http.routers.portnomic-app.entrypoints=https"
```

**Cert resolver:** If your Traefik uses a different Let's Encrypt cert resolver, edit:
```yaml
- "traefik.http.routers.portnomic-app.tls.certresolver=letsencrypt"
```
Change `letsencrypt` to your resolver name (e.g. `le`, `acme`). If you don't use a resolver, remove that line.

---

## Directory layout on VPS

```
/opt/portnomic/          # Your main public website (existing)
/opt/portnomic-app/      # Portnomic app (this deployment)
```

---

## Updating the app

```bash
cd /opt/portnomic-app
git pull
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml build --no-cache app
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml up -d app
docker compose -f docker-compose.prod-simple.yml -f docker-compose.traefik.yml exec app alembic upgrade head
```

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| 502 Bad Gateway | App container running? `docker ps` |
| 404 from Traefik | Host rule matches? Network correct? |
| CORS errors | `CORS_ORIGINS` includes `https://app.portnomic.com` |
| DB connection failed | `DATABASE_URL` uses `postgres` host, not `localhost` |
| OAuth redirect fails | `OAUTH_REDIRECT_BASE_URL` and `OAUTH_FRONTEND_SUCCESS_URL` correct |
