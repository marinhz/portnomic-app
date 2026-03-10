# Task 6.12 — Custom SMTP integration: better error handling, test connection, hide Outlook

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

1. Improve error handling when adding a new custom SMTP integration so users get clear, actionable feedback.
2. Add a "Test connection" option to validate credentials before saving.
3. Hide the "Connect Outlook" button for now (can be re-enabled later via feature flag or config).

---

## Scenario

> User wants to handle errors better when adding a new custom SMTP integration. They want test connection options and to hide the Connect Outlook option for now.

---

## Problem statement

- **Current state:** When adding a custom integration (IMAP or future per-tenant SMTP), errors are generic (e.g. "Failed to add IMAP connection"). Users cannot verify credentials before saving. The Connect Outlook button is always visible.
- **Pain:** Users struggle to diagnose connection failures (wrong host, port, auth, firewall). They may save invalid credentials and only discover issues during sync. Outlook option may not be ready for production use.
- **Goal:** Clear, specific error messages; ability to test connection before saving; temporarily hide Outlook from the UI.

---

## Scope

### 1. Better error handling

- **Backend:** When `POST /api/v1/integrations/email/imap` fails, return structured error responses with:
  - **Specific error codes/messages** where possible (e.g. `connection_refused`, `auth_failed`, `timeout`, `invalid_host`)
  - Map common exceptions (e.g. `smtplib.SMTPAuthenticationError`, `socket.timeout`, `ConnectionRefusedError`) to user-friendly messages
  - Include `detail` or `error_code` in `ErrorResponse` for frontend to display
- **Frontend:** In `IntegrationsPage.tsx`, display the backend error message in the form area (not just toast), e.g. in an `Alert` below the form. Preserve form values on error so the user can correct and retry without re-entering.

### 2. Test connection option

- **Backend:** Add `POST /api/v1/integrations/email/imap/test` — accepts same body as create (`imap_host`, `imap_port`, `imap_user`, `imap_password`). Attempts a quick IMAP login (connect + authenticate, no full sync). Returns `{ "ok": true }` or `{ "ok": false, "error": "..." }`. Does not persist credentials. Same permission as add (`admin:users`).
- **Frontend:** Add a "Test connection" button next to "Add IMAP Connection" in the IMAP form. On click, call the test endpoint with current form values. Show success toast or inline error. Disable "Add IMAP Connection" until test passes (optional) or allow add regardless — test is advisory.
- **Note:** If a future custom SMTP (outbound) integration is added, apply the same pattern: `POST /integrations/email/smtp/test` for SMTP.

### 3. Hide Connect Outlook

- **Frontend:** In `IntegrationsPage.tsx`, hide the "Connect Outlook" button. Options:
  - **A) Remove** the button entirely (simplest).
  - **B) Feature flag** — e.g. `SHOW_OUTLOOK_CONNECT` env or config; hide when false (default).
  - **C) CSS `hidden`** — keep in DOM but visually hidden for quick re-enable.
- **Recommendation:** Use option B (feature flag) so Outlook can be re-enabled without code change. If no feature-flag infra exists, use option A (remove) with a code comment: `// Outlook hidden per Task 6.12; re-add when ready`.

---

## Acceptance criteria

### Error handling

- [ ] Backend returns specific error messages for common IMAP failures (auth, timeout, connection refused, invalid host).
- [ ] Frontend shows the error in an Alert below the form (not only toast).
- [ ] Form values are preserved when add fails; user can correct and retry.

### Test connection

- [ ] `POST /api/v1/integrations/email/imap/test` exists and validates credentials without persisting.
- [ ] Frontend has a "Test connection" button in the IMAP form.
- [ ] Test success shows a success toast or inline message.
- [ ] Test failure shows the backend error message inline.

### Hide Outlook

- [ ] "Connect Outlook" button is not visible on the Integrations page.
- [ ] Gmail and Add IMAP remain visible and functional.
- [ ] (If feature flag) Outlook can be re-enabled via config without code change.

---

## Technical notes

| Area | File(s) |
|------|---------|
| IMAP add API | `backend/app/routers/integrations.py` |
| Mail connection service | `backend/app/services/mail_connection.py` |
| Integrations page | `frontend/src/pages/settings/IntegrationsPage.tsx` |
| Error response schema | `backend/app/schemas/common.py` (ErrorResponse) |

---

## Out of scope (for this task)

- Per-tenant custom SMTP (outbound) — current scope is IMAP ingest; SMTP outbound remains global config.
- Re-enabling Outlook — only hide for now; separate task when ready.
