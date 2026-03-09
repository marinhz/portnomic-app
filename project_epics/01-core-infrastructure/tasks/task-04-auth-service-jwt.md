# Task 1.4 — Auth service (login, JWT issue/validate/refresh)

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Implement authentication: login with email + password, JWT access token (short-lived) and refresh token, and token validation/refresh (EDD §6.2).

## Scope

- **POST /auth/login** — Email + password → access_token, refresh_token, expires_in, requires_mfa (EDD §7.2).
- **POST /auth/refresh** — Refresh token → new access token.
- JWT validation middleware/dependency for protected routes.
- Secrets (JWT secret, algorithm, expiry) from config/secret manager.

## Acceptance criteria

- [ ] Login returns tokens or indicates MFA required; invalid credentials return 401.
- [ ] Access token short-lived (e.g. 15 min); refresh token longer; both validated correctly.
- [ ] Refresh endpoint issues new access token for valid refresh token.
- [ ] All protected endpoints require valid JWT; 401 when missing or invalid.
