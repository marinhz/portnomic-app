# Task 1.19 — Session persistence review (survive refresh)

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Review and fix frontend session behaviour so that the user stays logged in across page refreshes and browser tabs. Currently, access and refresh tokens are stored only in memory (`api/client.ts`), so a full page reload clears them and the user is redirected to login.

## Scope

- **Root cause:** `frontend/src/api/client.ts` keeps `accessToken` and `refreshToken` in module-level variables. These are lost on refresh; `AuthContext` then sees no token and does not restore the user.
- **Fix:** Persist tokens in a durable store and rehydrate on app load.
  - Prefer **sessionStorage** for “single tab” session (cleared when tab closes) or **localStorage** for “remember me” across tabs/restarts. Document the choice (security vs UX).
  - On app init, read stored tokens, set them on the API client (`setTokens`), then let `AuthContext` call `/auth/me` to restore user. If `/auth/me` returns 401, clear stored tokens and redirect to login.
- **Security:** Do not log or expose tokens in URLs or client-side error messages. Consider httpOnly cookies as a future option (would require backend changes).
- **Edge cases:** Logout must clear the persisted store. Refresh-token flow (401 → refresh → retry) should update stored tokens if the backend returns a new refresh token. MFA flow already uses the same `setTokens`; ensure post-MFA tokens are also persisted.
- Optional: short doc in README or CONTRIBUTING on how auth/session works on the frontend.

## Acceptance criteria

- [x] After login (and after MFA if used), tokens are stored in the chosen storage (sessionStorage or localStorage).
- [x] On full page refresh, tokens are read from storage and the user remains on the current (or home) page without being sent to login, provided the tokens are still valid.
- [x] Logout clears stored tokens and in-memory state.
- [x] If stored token is invalid/expired and refresh fails, user is redirected to login and stored tokens are cleared.
- [x] No tokens appear in the URL, in console logs, or in user-facing error messages.

## References

- `frontend/src/api/client.ts` — token variables and `setTokens` / `clearTokens` / `getAccessToken`.
- `frontend/src/auth/AuthContext.tsx` — initial load uses `getAccessToken()` then fetches `/auth/me`; login/MFA call `setTokens`.
- Epic 1 scope: “Auth service: … JWT issue/validate/refresh; short-lived access token, refresh token”.
