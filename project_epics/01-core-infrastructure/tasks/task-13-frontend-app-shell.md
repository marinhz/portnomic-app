# Task 1.13 — Frontend app shell

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

React app shell with routing, auth state, tenant context, and layout so unauthenticated users are redirected to login and authenticated users see tenant-aware UI (EDD §4.1).

## Scope

- React 18+; React Router for routing (hash or browser history).
- Auth state (logged-in user, tokens); tenant context from authenticated user (no tenant_id in URL).
- Layout component(s); protected routes that redirect to login when not authenticated.
- Placeholder or minimal dashboard view.

## Acceptance criteria

- [ ] Unauthenticated access to protected routes redirects to login.
- [ ] After login, user sees app shell with tenant context set; tokens stored (memory and/or httpOnly cookie for refresh).
- [ ] Layout is responsive and ready for dashboard/vessel/port call/admin views.
