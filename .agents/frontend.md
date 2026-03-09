# Frontend Agent — ShipFlow AI

Use with **react-dev**, **react-router-v7**, and **tailwind-design-system**. Applies to React SPA, routing, auth UI, and tenant-aware screens.

## Structure

- **App shell:** Routing, auth state, tenant context, layout (React 18+, React Router).
- **Auth UI:** Login, MFA challenge, password reset (secure forms).
- **Dashboard:** Vessels, port calls, DA list, KPIs (data tables, charts).
- **Vessel / Port call:** CRUD and detail views (forms).
- **DA workspace:** Proforma/Final DA view, approve, PDF preview, send.
- **Admin:** User/role management (tenant-scoped, RBAC-driven UI).
- **API client:** HTTP client with JWT attach, refresh on 401, centralized error handling (e.g. Axios/fetch + interceptors).

## Conventions

- SPA with browser or hash routing; tokens in memory and optionally httpOnly cookie for refresh.
- Tenant comes from authenticated user only — no `tenant_id` in URL.
- All API calls through one client: `Authorization: Bearer <access_token>`; on 401 try refresh or re-login.
- Responsive UI; design system and Tailwind for consistency.

## Key Flows

- **Login → MFA (if required) → Dashboard** with tenant context set.
- **List/detail for vessels, port calls, DAs** with tenant-scoped API calls.
- **DA workflow:** View Proforma/Final → Approve → Send (PDF + email); reflect status from API.
- **Admin:** List/create/edit users and roles according to `admin:users` / `admin:roles` permissions.

## Data & API

- Use loaders/actions (React Router v7) for data-driven routes where applicable.
- Handle pagination and filters (e.g. `vessel_id`, `status`) for port calls and DA list.
- Show clear loading and error states; no sensitive data in error messages.
