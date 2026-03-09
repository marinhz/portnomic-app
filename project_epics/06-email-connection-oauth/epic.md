# Epic 6 — Email Connection (OAuth 2.0 & UI)

**Source:** Gap from current implementation; Enterprise Technical Specification (email OAuth 2.0 flow).  
**Duration (estimate):** 3–4 weeks

---

## Objective

Allow tenants (or tenant admins) to connect their own mailboxes for email ingest via OAuth 2.0 (Gmail, Microsoft 365/Outlook) and optional IMAP, with a dedicated Settings / Integrations UI. Ingest pipeline uses per-tenant connections instead of only a single global IMAP mailbox.

---

## Scope

### Data model

- **Mail connection** entity: tenant-scoped; provider (gmail | outlook | imap); encrypted credentials (OAuth access/refresh tokens or IMAP password); optional display email; status (connected | error); created_at / updated_at.
- Uniqueness: one connection per provider per tenant (or allow multiple per tenant if needed for multiple mailboxes).
- Migrations: new table(s); use existing secrets/encryption patterns (e.g. MFA secret style) for token storage.

### OAuth 2.0 backend

- **Google (Gmail):** OAuth 2.0 authorization code flow; scopes for read mail (e.g. `https://www.googleapis.com/auth/gmail.readonly` or `gmail.modify`); config: client_id, client_secret, redirect_uri via env/settings.
- **Microsoft (Outlook / Microsoft 365):** OAuth 2.0 authorization code flow; scopes for Mail.Read; config: client_id, client_secret, redirect_uri, tenant (common or org-specific).
- Endpoints: **initiate** — `GET /api/v1/integrations/email/connect?provider=gmail|outlook` (redirect to provider consent URL with state); **callback** — `GET /api/v1/integrations/email/callback` (exchange code for tokens, store encrypted, redirect to frontend success).
- State parameter: bind to tenant_id and user session to prevent CSRF and ensure tenant context.

### Token storage and refresh

- Store access_token and refresh_token (encrypted) with expiry; refresh before use when expired using refresh_token.
- Background job or on-demand refresh; on refresh failure mark connection as error and optionally notify.

### Ingest from connected mailboxes

- Worker (or scheduled job): for each tenant with a connected mailbox (Gmail API or Microsoft Graph, or IMAP), fetch new messages since last sync; persist to Email table with tenant_id; enqueue parse job; idempotency via (tenant_id, external_id).
- Support both OAuth-based (Gmail API, Graph API) and IMAP connections; deprecate or keep global IMAP as fallback for backward compatibility.

### API

- **GET /api/v1/integrations/email** — List mail connections for current tenant (JWT, tenant-scoped, permission e.g. `integrations:read` or `admin:users`).
- **DELETE /api/v1/integrations/email/{id}** — Disconnect (revoke stored tokens / clear credentials).
- Optional: **POST /api/v1/integrations/email/imap** — Add IMAP connection (host, user, encrypted password) for tenants that prefer IMAP over OAuth.

### Frontend (Settings / Integrations UI)

- New route: e.g. `/settings/integrations` or `/settings/email` under protected layout.
- Page: “Email for ingest” — show connected mailboxes (provider, email, status); buttons “Connect Gmail”, “Connect Outlook”; optional “Add IMAP” form.
- “Connect Gmail” / “Connect Outlook” → redirect to backend initiate URL → user completes OAuth on provider → callback redirects back to app with success/error → frontend shows updated list.
- Disconnect button per connection; confirm before revoke.

### Security and compliance

- Tokens and IMAP passwords encrypted at rest; never log tokens.
- RBAC: only certain roles (e.g. tenant admin) can add/remove email connections.
- Audit log: “mail_connection_added”, “mail_connection_removed” with tenant_id and provider (no credentials).

---

## Out of scope (for this epic)

- Sending mail via OAuth (outbound remains SMTP unless a later epic adds it).
- User-level connections (only tenant-level in this epic unless specified otherwise).
- Native mobile app OAuth flows.

---

## Acceptance criteria

- [ ] Tenant admin can open Settings → Integrations (or Email) and see “Connect Gmail” / “Connect Outlook”.
- [ ] OAuth flow completes and connection appears in list with status “connected”.
- [ ] Worker ingests new emails from connected OAuth mailboxes (Gmail API / Graph) and optionally tenant IMAP; emails stored with correct tenant_id and enqueued for parse.
- [ ] Token refresh runs so connections stay valid; failed refresh marks connection as error.
- [ ] Tenant admin can disconnect a mailbox; stored tokens/credentials are removed.
- [ ] All token and password storage is encrypted; audit events recorded for connect/disconnect.
- [ ] Existing global IMAP/webhook ingest continues to work (backward compatible).

---

## EDD / doc references

- EDD §4.2 Email ingest service; §5.1 Email entity; §7.4, §8.1 ingest and parse.
- EDD §6.1 Encryption (secrets); §6.4 Audit.
- Project epics: 02-ai-processing (email ingest, worker); 01-core-infrastructure (auth, RBAC).
