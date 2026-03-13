# Task 2.15 — AI Integration Connection Test: Better Error Handling

**Epic:** [02-ai-processing](../epic.md)

---

## Scenario

User reports that the AI integration connection test always returns "Connection successful" even when credentials are invalid or the LLM service is unreachable. Implement better error handling so the test accurately reflects connection status and surfaces actionable error messages.

---

## Objective

Fix the AI integration connection test so it:
1. Correctly validates credentials and connectivity
2. Returns meaningful, user-facing error messages for failures
3. Optionally tests with **unsaved** config (credentials entered in form but not yet saved) so users can verify before saving

---

## Scope

### Backend

- **`POST /api/v1/settings/ai/test`** — Improve error handling:
  - Accept optional request body with `api_key`, `base_url`, `model` to test **unsaved** config (credentials from form before save).
  - If body provided, use those values for the test instead of DB/platform config.
  - Map specific exceptions to user-friendly messages:
    - `APIConnectionError` → "Cannot reach AI service. Check base URL and network."
    - `APITimeoutError` → "Request timed out. AI service may be slow or unreachable."
    - `RateLimitError` → "Rate limit exceeded. Try again later."
    - `AuthenticationError` (401) → "Invalid API key. Check your credentials."
    - Invalid URL / DNS → "Invalid base URL. Check the endpoint address."
  - Return structured error response: `{ "code": "...", "message": "..." }` for frontend display.
  - Ensure no silent success when the actual call fails (e.g. wrong config being used).

### Frontend

- **AISettingsPage** — Improve test connection UX:
  - When user clicks "Test connection", send unsaved form values (`api_key`, `base_url`, `model`) in the request body if they differ from saved config.
  - Display the API error message in the toast and/or inline error area.
  - Show loading state during test; disable "Test" button while testing.
  - Consider showing success details (e.g. "Connected to {model}") on success.

---

## Acceptance criteria

- [ ] Test connection uses unsaved form credentials when provided (test-before-save).
- [ ] Invalid API key returns a clear "Invalid API key" message, not "Connection successful".
- [ ] Unreachable base URL / timeout returns a clear error, not success.
- [ ] Rate limit and auth errors are mapped to user-friendly messages.
- [ ] Frontend displays the backend error message to the user.
- [ ] Success only shown when the LLM actually responds successfully.

---

## Priority

High — User trust and correct configuration validation are critical for AI features.
