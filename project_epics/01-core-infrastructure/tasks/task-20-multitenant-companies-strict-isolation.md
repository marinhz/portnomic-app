# Task 1.20 — Multitenant: Add Companies & Strict Tenant Isolation

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Enable adding new companies (tenants) via API and UI, and ensure data is strictly isolated per tenant with no cross-tenant access. Build on existing tenant middleware and tenant-scoped services.

---

## Problem statement

- **Current state:** Tenants exist in the schema and are used for isolation, but there is no way to create new tenants. Tenants are created via seed scripts or migrations. Data isolation is enforced at the application layer via `get_tenant_id` from JWT.
- **Pain:** Cannot onboard new companies without manual DB operations; need verification that no cross-tenant data leaks exist.
- **Goal:** Platform admin can add new companies; all data strictly scoped per tenant; optional defense-in-depth (e.g. PostgreSQL RLS).

---

## Scope

### 1. Platform admin / super-admin

- Introduce a **platform admin** concept: a user who can manage tenants (companies) across the system.
- **Options:**
  - **A:** Environment variable `PLATFORM_ADMIN_EMAILS` (comma-separated) — users with these emails can access platform admin endpoints.
  - **B:** `is_platform_admin` flag on User (requires migration).
  - **C:** Special role `platform_admin` in a system tenant (e.g. first tenant).
- **Recommendation:** Start with Option A (env var) for simplicity; no schema change. Later migrate to B or C if needed.

### 2. Tenant (company) management API

- **POST /platform/tenants** — Create new tenant (platform admin only).
  - Body: `{ "name": "Acme Shipping", "slug": "acme-shipping" }`
  - Slug: unique, URL-safe (lowercase, hyphens). Used for inbound email routing (`inbound+<slug>@shipflow.ai`).
  - On create: optionally create default role(s) for the tenant (e.g. `admin`, `viewer`).
- **GET /platform/tenants** — List tenants (platform admin only; paginated).
- **GET /platform/tenants/{id}** — Get tenant by ID (platform admin only).
- **PATCH /platform/tenants/{id}** — Update tenant name/settings (platform admin only).
- **POST /platform/tenants** — Optionally accept `initial_admin_email` and `initial_admin_password` to create first admin user for the new tenant (creates user + admin role in one flow).

### 3. Tenant service (backend)

- `TenantService` with:
  - `create_tenant(db, name, slug, settings?, initial_admin?)`
  - `list_tenants(db, page, per_page)`
  - `get_tenant(db, tenant_id)`
  - `update_tenant(db, tenant_id, data)`
- Slug validation: `^[a-z0-9][a-z0-9-]*[a-z0-9]$` or similar; reject reserved slugs (`admin`, `platform`, `api`, etc.).
- On tenant create: create default roles (e.g. `admin` with `admin:users`, `admin:roles`, etc.; `viewer` with read-only).

### 4. Platform admin dependency

- `get_platform_admin` dependency: checks JWT, then verifies user email is in `PLATFORM_ADMIN_EMAILS` (or equivalent). Returns 403 if not.
- Platform routes use `Depends(get_platform_admin)` instead of `Depends(get_tenant_id)`.

### 5. Add company UI (frontend)

- **Route:** `/platform/tenants` or `/admin/companies` (behind platform admin check).
- **List view:** Table of tenants (name, slug, created_at, user count).
- **Create form:** Name, slug (auto-derived from name or editable), optional initial admin email/password.
- **Detail view:** Tenant info, link to manage users (or redirect to tenant context).

### 6. Strict tenant isolation verification

- **Audit all tenant-scoped entities:** Ensure every query filters by `tenant_id`. Entities: User, Role, Vessel, Port, PortCall, Email, ParseJob, DisbursementAccount, Tariff, MailConnection, AuditLog.
- **Port model:** `tenant_id` is nullable — clarify: shared reference ports vs tenant-specific. If shared, ensure no tenant data leaks through ports.
- **Checklist:** Grep for `select(...).where(` without `tenant_id` in tenant-scoped services; fix any omissions.
- **Integration test:** Create two tenants, add data to each; verify Tenant A cannot access Tenant B's data via API (use different JWTs).

### 7. Optional: PostgreSQL Row Level Security (RLS)

- **If scope allows:** Add RLS policies on tenant-scoped tables so that even raw SQL or misconfigured queries cannot return cross-tenant data.
- Policy: `USING (tenant_id = current_setting('app.tenant_id')::uuid)`.
- Set `app.tenant_id` in middleware before each request; clear after.
- **Note:** Requires careful session handling; may add complexity. Defer if time-constrained.

---

## Acceptance criteria

- [ ] Platform admin can create a new tenant via `POST /platform/tenants` with name and slug.
- [ ] Platform admin can list and view tenants via `GET /platform/tenants` and `GET /platform/tenants/{id}`.
- [ ] New tenant gets default roles (e.g. `admin`, `viewer`) on creation.
- [ ] Optional: Platform admin can create tenant with initial admin user in one request.
- [ ] Slug is validated (unique, URL-safe); reserved slugs rejected.
- [ ] Frontend: Platform admin can add a new company via UI (list + create form).
- [ ] All tenant-scoped services and queries include `tenant_id` filter; no cross-tenant data access.
- [ ] Integration test proves Tenant A cannot access Tenant B's vessels, port calls, users, etc.
- [ ] Audit log records tenant creation (tenant_id, actor, action).

---

## Implementation notes

### Tenant create schema

```python
# schemas/tenant.py
class TenantCreate(BaseModel):
    name: str
    slug: str
    initial_admin_email: str | None = None
    initial_admin_password: str | None = None

class TenantResponse(BaseModel):
    id: uuid.UUID
    name: str
    slug: str
    created_at: datetime
```

### Platform admin dependency

```python
# dependencies/platform.py
def get_platform_admin(
    current_user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    admin_emails = [e.strip() for e in settings.platform_admin_emails.split(",") if e.strip()]
    if current_user.email not in admin_emails:
        raise HTTPException(403, "Platform admin access required")
    return current_user
```

### Default roles on tenant create

```python
DEFAULT_ROLES = [
    {"name": "admin", "permissions": ["admin:users", "admin:roles", "vessel:read", "vessel:write", ...]},
    {"name": "viewer", "permissions": ["vessel:read", "port_call:read", ...]},
]
```

### Entities to verify for tenant_id

| Entity            | tenant_id | Notes                    |
|-------------------|-----------|--------------------------|
| User              | ✓         |                          |
| Role              | ✓         |                          |
| Vessel            | ✓         |                          |
| Port              | nullable  | Clarify shared vs tenant |
| PortCall          | ✓         |                          |
| Email             | ✓         |                          |
| ParseJob          | ✓         |                          |
| DisbursementAccount | ✓       |                          |
| Tariff            | ✓         |                          |
| MailConnection    | ✓         |                          |
| AuditLog          | ✓         |                          |

---

## Related code

- `backend/app/models/tenant.py` — Tenant model
- `backend/app/dependencies/tenant.py` — get_tenant_id, require_valid_tenant
- `backend/app/routers/admin.py` — tenant-scoped admin (users, roles)
- `backend/app/config.py` — add `platform_admin_emails: str`
- All services: vessel_svc, port_call_svc, email_service, etc. — verify tenant_id in every query

---

## Dependencies

- **Task 1.4** (Auth, JWT) — platform admin needs authenticated user.
- **Task 1.6** (Tenant middleware) — existing tenant resolution; platform routes bypass tenant scope.
- **Task 1.10** (Admin service) — pattern for CRUD; tenant service is similar but platform-scoped.

---

## Out of scope (for now)

- Tenant deletion (cascade is complex; soft-delete or deactivation later).
- Tenant-specific branding or custom domains.
- Billing or subscription per tenant.
- PostgreSQL RLS (optional; can be a follow-up task).
