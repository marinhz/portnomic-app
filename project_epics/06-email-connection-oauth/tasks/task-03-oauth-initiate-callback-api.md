# Task 6.3 — OAuth initiate and callback API

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Expose API endpoints to start the OAuth flow (redirect user to provider) and handle the callback (exchange code, store connection, redirect to frontend).

## Scope

- **Initiate:** `GET /api/v1/integrations/email/connect?provider=gmail|outlook` — requires JWT (and permission e.g. `integrations:write` or tenant admin). Build state (e.g. signed or encrypted payload with tenant_id, user_id, csrf); redirect to provider’s authorization URL with client_id, redirect_uri, scope, state, response_type=code.
- **Callback:** `GET /api/v1/integrations/email/callback?code=...&state=...` — no JWT (user lands here from provider). Validate state; exchange code for tokens; create or update mail_connection for tenant; encrypt and store tokens; redirect to frontend success URL (e.g. `/settings/integrations?email=connected`) or error URL with message.
- State must be bound to current tenant/user so callback cannot be used to attach a mailbox to another tenant.
- Errors: invalid state, code exchange failure, missing config — redirect to frontend with query params or fragment for error message.

## Acceptance criteria

- [ ] Calling connect with provider=gmail or outlook redirects to correct provider consent screen.
- [ ] After user approves, callback exchanges code and persists encrypted tokens; redirect to frontend.
- [ ] Invalid or reused state/code do not create connection; user sees error.
- [ ] Only authenticated users with required permission can hit connect; callback is public but state ties to session/tenant.
