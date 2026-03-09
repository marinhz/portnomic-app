# Task 6.11 — Admin delete email from UI

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Allow tenant admins to delete individual emails from the system via the UI. This enables admins to remove spam, test data, or incorrectly ingested emails.

---

## Problem statement

- Emails are ingested from connected mailboxes and stored indefinitely.
- There is no way for admins to remove unwanted emails (spam, duplicates, test data) from the UI.
- GDPR and data hygiene require the ability to delete emails when appropriate.

---

## Scope

### 1. Backend API

- **Endpoint:** `DELETE /api/v1/emails/{email_id}`
- **Permission:** `admin:users` (tenant admin only; operators with `ai:parse` cannot delete).
- **Behavior:** Delete the email and cascade to related `parse_jobs` (FK `ondelete="CASCADE"`).
- **Response:** 204 No Content on success.
- **Errors:** 404 if email not found or not in tenant; 403 if user lacks permission.
- **Implementation:** Add `delete_email` to `email_service.py`; add route in `emails.py` router.

### 2. Delete strategy

- **Option A (recommended):** Hard delete — remove row from `emails`; parse_jobs cascade automatically.
- **Option B:** Soft delete — add `deleted_at` column; filter deleted emails from list/get; consider for audit trail. (Out of scope unless explicitly required.)

### 3. Frontend — Email detail page

- **Location:** `EmailDetail.tsx`
- **UI:** "Delete email" button (e.g. red/destructive style), visible only to admins.
- **Flow:** Click → confirmation modal ("Are you sure you want to delete this email? This cannot be undone.") → on confirm, call `DELETE /emails/{id}` → redirect to `/emails` on success.
- **Permission:** Check `admin:users` or equivalent; hide button if user lacks permission. (Frontend may rely on API 403 if permission check is complex.)

### 4. Frontend — Email list (optional)

- **Location:** `EmailList.tsx`
- **UI:** Per-row "Delete" action (icon or dropdown) for admins; same confirmation flow.
- **Alternative:** Delete only from detail page to keep list simpler; can add list delete in a follow-up.

### 5. Audit

- **Event:** `email_deleted` — log tenant_id, email_id, user_id, subject (truncated) for compliance.
- **Implementation:** Use existing audit pattern if present; otherwise log to application logs.

---

## Acceptance criteria

- [ ] `DELETE /api/v1/emails/{email_id}` exists and requires `admin:users`.
- [ ] Deleting an email removes it and its parse_jobs from the database.
- [ ] 404 returned when email not found or belongs to another tenant.
- [ ] Email detail page shows "Delete email" button for admins.
- [ ] Confirmation modal prevents accidental deletion.
- [ ] On successful delete, user is redirected to `/emails`.
- [ ] Audit or log records email deletion (tenant, email_id, user).

---

## Related code

- `backend/app/routers/emails.py` — add DELETE route
- `backend/app/services/email_service.py` — add `delete_email`
- `backend/app/models/email.py` — Email model; parse_jobs relationship with CASCADE
- `frontend/src/pages/emails/EmailDetail.tsx` — add delete button and confirmation
- `frontend/src/pages/emails/EmailList.tsx` — optional per-row delete
- `backend/app/dependencies/rbac.py` — `RequirePermission("admin:users")`

---

## Dependencies

- [Task 6.5](task-05-ingest-from-oauth-mailboxes.md) — Ingest from OAuth mailboxes
- [Task 6.7](task-07-settings-integrations-ui.md) — Settings / Integrations UI (admin patterns)
