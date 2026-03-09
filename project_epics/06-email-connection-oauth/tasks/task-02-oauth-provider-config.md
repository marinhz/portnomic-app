# Task 6.2 — OAuth 2.0 provider config (Google, Microsoft)

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Add backend configuration for Google (Gmail) and Microsoft (Outlook / Microsoft 365) OAuth 2.0 so the app can build authorization URLs and exchange codes for tokens.

## Scope

- Settings (e.g. in `config.py` or dedicated module): Google — `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_BASE_URL` (or full redirect_uri); Microsoft — `MICROSOFT_OAUTH_CLIENT_ID`, `MICROSOFT_OAUTH_CLIENT_SECRET`, `MICROSOFT_OAUTH_TENANT` (common or org id), same redirect base.
- Scopes: Gmail — `https://www.googleapis.com/auth/gmail.readonly` (or gmail.modify if needed); Microsoft — `https://graph.microsoft.com/Mail.Read`, `offline_access`.
- No routes yet; only config and helper to build auth URL and (in next task) exchange code for tokens. Use standard OAuth 2.0 authorization code flow (PKCE optional but recommended for public clients; for backend-only redirect, state is mandatory).
- Document in README or ops doc: how to create Gmail/Outlook app and set redirect URI.

## Acceptance criteria

- [ ] Config loads from env; missing optional OAuth vars do not crash app (feature disabled if not set).
- [ ] Helper can build Google and Microsoft authorization URLs with state and redirect_uri.
- [ ] Helper can exchange authorization code for access_token and refresh_token (Google token endpoint, Microsoft token endpoint).
