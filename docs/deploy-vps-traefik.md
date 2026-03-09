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

The config uses the `web` network (common for Traefik). If your Traefik uses a different network (e.g. `traefik`, `proxy`), edit `docker-compose.traefik.yml` and change `web` to match.

---

## Step 4: Create production `.env`

```bash
cp .env.production.example .env
nano .env   # or vim
```

Replace all `YOUR_*` placeholders. Generate secrets:

```bash
# POSTGRES_PASSWORD, JWT_SECRET, WEBHOOK_INBOUND_SECRET
openssl rand -base64 32

# MFA_ENCRYPTION_KEY, OAUTH_STATE_ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Required:** `POSTGRES_PASSWORD`, `JWT_SECRET`, `MFA_ENCRYPTION_KEY`. Use the same `POSTGRES_PASSWORD` in both `DATABASE_URL` and `DATABASE_URL_SYNC`.

**Optional:** `LLM_API_KEY`, `GOOGLE_OAUTH_*`, `SMTP_*`, `OAUTH_STATE_ENCRYPTION_KEY`, `WEBHOOK_INBOUND_SECRET`

---

## Step 5: Build and start

**Use the Traefik compose file only** (standalone – no port 80 binding, no conflict with main site).

```bash
docker compose -f docker-compose.traefik.yml build --no-cache
docker compose -f docker-compose.traefik.yml up -d
```

---

## Step 6: Run database migrations

```bash
docker compose -f docker-compose.traefik.yml exec app alembic upgrade head
```

---

## Step 7: (Optional) Seed initial data

```bash
docker compose -f docker-compose.traefik.yml exec app python -m app.seed
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
docker compose -f docker-compose.traefik.yml build --no-cache app
docker compose -f docker-compose.traefik.yml up -d app
docker compose -f docker-compose.traefik.yml exec app alembic upgrade head
```

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| 502 Bad Gateway | App container running? `docker ps -a` |
| 404 from Traefik | Host rule matches? Network correct? |
| CORS errors | `CORS_ORIGINS` includes `https://app.portnomic.com` |
| DB connection failed | `DATABASE_URL` uses `postgres` host, not `localhost` |
| OAuth redirect fails | `OAUTH_REDIRECT_BASE_URL` and `OAUTH_FRONTEND_SUCCESS_URL` correct |
