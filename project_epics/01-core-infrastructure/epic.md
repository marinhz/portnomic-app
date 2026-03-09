# Epic 1 — Core Infrastructure

**Source:** SHIPFLOW_AI_Engineering_Design_Document.md, Implementation Roadmap Phase 1  
**Duration (estimate):** 2 weeks

---

## Objective

Deliver the foundational platform: database, authentication, tenant middleware, RBAC, base API, and frontend shell so that all subsequent epics build on a secure, multi-tenant base.

---

## Scope

### Data layer

- **PostgreSQL** as primary store; all tenant-scoped tables include `tenant_id`.
- **Alembic** migrations; versioned schema; composite indexes `(tenant_id, <main_lookup>)`.
- Core entities for this epic: **Tenant**, **User**, **Role**, **Vessel**, **Port**, **PortCall** (EDD §5.1).
- **Redis** for session and idempotency keys; optional cache-aside keyed by `tenant_id`.

### Backend (FastAPI)

- **API gateway:** Routing, CORS, rate limiting, request ID (EDD §4.2).
- **Auth service:** Login (email + password), MFA (TOTP), JWT issue/validate/refresh; short-lived access token, refresh token (EDD §6.2).
- **Tenant middleware:** Resolve tenant from JWT; inject into request context (dependency).
- **RBAC middleware:** Check permission for (user, resource, action), e.g. `vessel:read`, `vessel:write`, `port_call:read`, `admin:users` (EDD §6.2).
- **Vessel service:** CRUD vessels (tenant-scoped).
- **Port call service:** CRUD port calls, link to vessel.
- **Admin service:** User/role CRUD (tenant-scoped).
- **Audit logger:** Append-only audit events (who, what, when, resource_type, resource_id) (EDD §6.4).
- **OpenAPI 3.0** spec; consistent error envelope `{ "error": { "code", "message", "details" } }` (EDD §7.1).

### Frontend (React)

- **App shell:** Routing (React Router), auth state, tenant context, layout (EDD §4.1).
- **Auth UI:** Login, MFA challenge, password reset (secure forms).
- **API client:** HTTP client with JWT attach, refresh on 401, centralized error handling.
- **Dashboard:** Placeholder or minimal view for vessels, port calls (data tables ready for later epics).
- **Vessel / Port call:** CRUD and detail views (forms).
- **Admin:** User/role management (tenant-scoped, RBAC-driven visibility).

### Security (foundation)

- Input validation (Pydantic); no secrets or PII in logs (EDD §6.3).
- MFA secret encrypted in DB; secrets from secret manager (EDD §6.1).

---

## Out of scope (later epics)

- Email ingest, AI parsing, DA generation, PDF, email dispatch.
- Full observability (metrics/tracing) beyond basic health and request logging.

---

## Acceptance criteria

- [ ] User can register/login, complete MFA when required, and receive/refresh JWT.
- [ ] All API calls (except login/MFA/refresh) require JWT; tenant is resolved and enforced on every request.
- [ ] RBAC denies access when user lacks required permission; audit log records state-changing actions.
- [ ] Vessels and port calls are CRUD’d with strict tenant isolation; no cross-tenant data access.
- [ ] Admin can manage users and roles within the tenant.
- [ ] Frontend app shell loads with auth and tenant context; unauthenticated users are redirected to login.
- [ ] OpenAPI spec is published and error responses follow the standard envelope.

---

## EDD references

- §3 Architecture overview  
- §4.1 Presentation layer, §4.2 Application layer, §4.3 Data layer  
- §5 Data model & persistence  
- §6 Security design  
- §7.2 Core endpoints (auth, vessels, port-calls, admin)
