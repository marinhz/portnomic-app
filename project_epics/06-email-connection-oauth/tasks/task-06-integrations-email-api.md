# Task 6.6 — Integrations email API (list, disconnect)

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Provide REST API for the frontend to list a tenant’s mail connections and to disconnect (remove) a connection.

## Scope

- **GET /api/v1/integrations/email** — Returns list of mail connections for the current tenant (from JWT). Each item: id, provider, display_email (or masked), status, created_at; no credentials or tokens. Permission: e.g. `integrations:read` or role-based (tenant admin). Response schema: array of connection summary.
- **DELETE /api/v1/integrations/email/{id}** — Delete the mail_connection with given id if it belongs to the current tenant. Clear stored credentials; remove row or set status to disconnected. Permission: `integrations:write` or tenant admin. Return 204 or 200.
- Optional: **GET /api/v1/integrations/email/{id}** — Single connection detail (same fields as list item, no secrets).
- Audit: log “mail_connection_removed” (and “mail_connection_added” from callback) with tenant_id, connection id, provider; no credentials.

## Acceptance criteria

- [ ] List returns only current tenant’s connections; no credential data in response.
- [ ] Delete removes connection and credentials; only owner tenant can delete.
- [ ] Audit events recorded for disconnect (and for connect in Task 6.3).
- [ ] Unauthorized or wrong-tenant access returns 403/404 as appropriate.
