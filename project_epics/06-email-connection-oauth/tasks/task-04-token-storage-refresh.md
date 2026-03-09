# Task 6.4 — Token storage and refresh

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Securely store OAuth tokens (encrypted), and refresh access tokens when expired so connected mailboxes remain usable without re-authorization.

## Scope

- Persist access_token, refresh_token, expires_at (or equivalent) in mail_connection credentials blob; encrypt at rest using app encryption key (same pattern as MFA).
- **Refresh logic:** Before using a connection (e.g. in ingest worker), check expiry; if expired or near expiry (e.g. 5 min buffer), call provider’s token endpoint with refresh_token, get new access_token (and optionally new refresh_token); update stored credentials; then proceed.
- On refresh failure (e.g. 401, revoked): set connection status to `error`, store error_message; do not retry indefinitely. Optional: background job that periodically refreshes all connected OAuth connections to keep them warm.
- No logging of token values; log only tenant_id, connection id, and “refresh success” or “refresh failed”.

## Acceptance criteria

- [ ] Tokens are encrypted in DB; decryption only in service layer.
- [ ] Expired tokens are refreshed automatically when connection is used; updated credentials saved.
- [ ] If refresh fails, connection is marked error and failure is not propagated as success.
- [ ] No token or secret in logs or error responses.
