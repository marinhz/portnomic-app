# Task 3.12 — Fix DA PDF Generation: No Response When Sending

**Epic:** [03-financial-automation](../epic.md)

---

## Agent

Use the **Frontend** agent ([`.agents/frontend.md`](../../../.agents/frontend.md)) with **react-dev** skill for UI changes. Use the **Backend** agent for API/worker fixes if root cause is server-side.

---

## Problem

User reports that when trying to generate a PDF of a Disbursement Account, nothing happens. Only the message appears:

> "Enter recipient email addresses (comma-separated), or leave empty to skip email and just generate PDF."

After clicking "Confirm Send" (with or without email addresses), there is no visible outcome: no success feedback, no PDF download, no "View PDF" button appearing, and no error message.

---

## Scope

### 1. Root cause investigation

- **Frontend:** Verify `handleSend` in `DADetail.tsx` correctly calls `POST /da/{da_id}/send` with valid body (including empty `to_addresses` when user leaves email field empty).
- **API client:** Ensure request body is serialized correctly when `to_addresses` is `undefined` or empty array (e.g. `{}` vs `{ to_addresses: [] }`).
- **Backend:** Confirm `POST /da/{id}/send` accepts and processes requests; returns 202; background task `process_da_send` runs.
- **Worker:** Check `da_worker.process_da_send` completes successfully; PDF is generated, stored, and `pdf_blob_id` is set; DA status transitions to `sent`.
- **Storage:** Verify blob storage (e.g. local filesystem, S3) is configured and writable.

### 2. UX improvements

- Show clear loading state during send ("Generating PDF…" / "Sending…").
- On success: show success toast or inline message; refresh DA data so "View PDF" button appears when `pdf_blob_id` is set.
- On error: display error message from API (e.g. `INVALID_STATUS`, `DA_NOT_FOUND`, plan limits).
- Consider polling or WebSocket for async completion if 2-second delay is unreliable.

### 3. Edge cases

- DA not yet approved: "Send" button is hidden; ensure user cannot reach send flow for non-approved DA.
- Empty email field: backend should accept `to_addresses: []` and still generate PDF without sending email.
- Worker failure: surface error to user (e.g. via polling job status or error callback if design supports it).

---

## Acceptance criteria

- [ ] User can successfully generate PDF by clicking "Confirm Send" with or without email addresses.
- [ ] Loading state is visible during the request and background processing.
- [ ] On success, "View PDF" button appears (or user is notified that PDF is ready).
- [ ] On failure, user sees a clear error message (not silent failure).
- [ ] Root cause is identified and documented; fix is applied to prevent regression.

---

## Related code

- `frontend/src/pages/da/DADetail.tsx` — Send dialog, `handleSend`, `loadDA` refresh
- `backend/app/routers/da.py` — `POST /{da_id}/send`, `process_da_send` background task
- `backend/app/services/da_worker.py` — `process_da_send` (PDF generation, storage, email, mark sent)
- `backend/app/services/pdf_generator.py` — `generate_pdf`
- `backend/app/services/storage.py` — `store_blob`, `get_blob`
- `backend/app/schemas/disbursement_account.py` — `DASendRequest`

---

## Dependencies

- Epic 3 Tasks 3.7 (PDF worker), 3.8 (Email dispatch), 3.9 (Send API), 3.10 (DA workspace)
