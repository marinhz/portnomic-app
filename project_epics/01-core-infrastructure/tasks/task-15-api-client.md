# Task 1.15 — Frontend API client

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Single HTTP client that attaches JWT, handles 401 with refresh or re-login, and centralizes error handling (EDD §4.1).

## Scope

- Axios or fetch with interceptors: add `Authorization: Bearer <access_token>` to every request.
- On 401: attempt refresh (POST /auth/refresh); on refresh failure redirect to login.
- Parse error envelope `{ "error": { "code", "message", "details" } }` and surface to UI.
- Base URL and possibly tenant from config/context.

## Acceptance criteria

- [ ] All API calls go through this client; no raw fetch to API without auth.
- [ ] Token refresh is transparent when access token expires; user is only sent to login when refresh fails or is invalid.
- [ ] Errors are handled consistently (e.g. toast or inline message from error.message).
