# Task 4.3 — Application security review

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Review and harden application security: input validation, error messages, CORS, rate limiting (EDD §6.3).

## Scope

- **Input validation:** All inputs validated (Pydantic); no raw user input in queries or commands; sanitize for XSS if rendered in UI.
- **Output:** JSON responses; no sensitive data in error messages or stack traces in production.
- **CORS:** Whitelist of frontend origins only; no wildcard in production.
- **Rate limiting:** Per-tenant and per-user limits on auth and API endpoints; 429 when exceeded.
- Review auth endpoints (login, MFA, refresh) for brute-force and lockout.
- Document findings and apply fixes.

## Acceptance criteria

- [ ] Validation covers all API inputs; invalid input returns 422 with safe message.
- [ ] CORS and rate limits are correctly configured; production does not leak internals in errors.
- [ ] Auth endpoints have appropriate rate limiting and (if applicable) lockout.
