# Task 14.11 — Refactor Document Ingestion: Separate Manual Uploads from Email Parsing

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Frontend** and **Backend** agents with **react-dev**, **react-router-v7**, **tailwind-design-system**, and **fastapi-python** skills.

---

## Context

Currently, manually uploaded documents are routed through the EmailWorker pipeline and stored as Email records. This results in manual files appearing in the "Emails" module, which is incorrect and causes:

- **Data integrity issues:** The Sentinel audit cannot distinguish an invoice uploaded today from an email received 3 days ago.
- **Client trust issues:** Clients expect uploaded documents in a "Documents" or "Secure Vault" section, not mixed with daily email correspondence.
- **Scalability limits:** Adding future sources (e.g. API integrations with Port Authorities) would further conflate Email logic with document logic.

We need to **decouple Document Ingestion from Email Ingestion**.

---

## Objective

Refactor the system so that:

1. Manual uploads are stored as Documents, **never** as Emails.
2. The ParseWorker handles a generic Document abstraction and branches on source type.
3. Manual uploads appear only in the Port Call "Documents" tab, never in the Email Inbox.
4. Parsed results from manual uploads trigger Sentinel and update the Port Call Dashboard correctly.

---

## Scope

### 1. Database & Logic Changes

#### Source differentiation

- Add a **`Document`** table (new entity) with:
  - `source_type`: enum `['EMAIL', 'MANUAL_UPLOAD']` (or extend to `API` later).
  - Core fields: `tenant_id`, `port_call_id`, `filename`, `content_hash` or `storage_key`, extracted text, `processing_status`, `ai_raw_output`, etc.
- **OR** if reusing Email: add `source_type` to the Email table and filter the Emails list to exclude `source_type == 'MANUAL_UPLOAD'`.

**Recommended:** Create a new `Document` table. Manual uploads create `Document` rows only; Email ingest continues to create `Email` rows. This cleanly separates concerns.

#### ParseJob refactor

- ParseJob currently references `email_id` only. Extend to support:
  - `document_id` (nullable) for manual uploads, **or**
  - Polymorphic: `target_type` (`'email'` | `'document'`), `target_id` (email_id or document_id).
- Worker picks up jobs and loads either Email or Document based on target type.

### 2. New API Endpoint

- **Endpoint:** `POST /api/v1/port-calls/{id}/upload`
- **Payload:** Multipart form with `file` + optional `category` (sof, da, noon_report).
- **Behavior:**
  1. Accept file and `port_call_id` directly.
  2. Validate file type (PDF, XLSX, JPG).
  3. Extract text; create `Document` row with `source_type='MANUAL_UPLOAD'`, `port_call_id`, `category`.
  4. **Do NOT** create an entry in the `emails` table.
  5. Enqueue ParseJob with `document_id` (or equivalent polymorphic target).
  6. Return job ID for status polling.

**Migration path:** Keep `POST /api/v1/port-calls/{id}/documents` as a deprecated alias that routes to the new flow, or remove it once the frontend is updated.

### 3. Worker Refactoring (ParseWorker)

- Refactor `ParseWorker` to handle a **generic document** (Email or Document).
- **If `source_type == 'MANUAL_UPLOAD'`:**
  - Skip all email-related metadata: Sender, Subject, Threading.
  - Use `port_call_id` from the request; no need to create/update PortCall from parsed data (port call already exists).
  - Immediately link parsed data (Invoices, SOF, Noon Reports) to the given `port_call_id`.
- **If source is Email:** preserve current behavior (resolve vessel/port, create/update port call, etc.).
- After parse completion: trigger Sentinel, leakage audit (for financial docs), and DA auto-create where applicable — same as today.

### 4. UI/UX Requirements

- **Location:** Manually uploaded files appear in a **"Documents"** or **"Files"** tab within the Port Call details, **never** in the Email Inbox.
- **Documents list:** Add `GET /api/v1/port-calls/{id}/documents` to fetch documents for a port call (excludes emails; or if using shared table with source_type, filter by `source_type='MANUAL_UPLOAD'`).
- **Status mapping:** When AI finishes parsing a manual upload, update:
  - Port Call Dashboard (e.g. tug costs, berthage days, DA line items).
  - Trigger The Sentinel (Audit Engine) immediately.
- **Emails list:** Filter out any records that are manual uploads. If using a separate Document table, the Emails API remains unchanged (no manual uploads there).

### 5. Acceptance criteria

- [ ] `Document` table (or equivalent) exists with `source_type` (`EMAIL` | `MANUAL_UPLOAD`).
- [ ] `POST /api/v1/port-calls/{id}/upload` accepts file + `port_call_id`; creates Document only, no Email row.
- [ ] ParseJob supports document-based jobs (e.g. `document_id` or polymorphic target).
- [ ] ParseWorker branches on source: for `MANUAL_UPLOAD`, skip email metadata; link parsed data to provided `port_call_id`.
- [ ] Manual uploads do **not** appear in the Emails module.
- [ ] Manual uploads appear in the Port Call Documents tab.
- [ ] Parsed results (Tug costs, Berthage days, DA, etc.) update the Port Call Dashboard.
- [ ] Sentinel (Audit Engine) runs after manual upload parse completion.
- [ ] Migration path for existing manual uploads (if stored as Emails today) is documented or handled.

---

## Related code

| Area | Path |
|------|------|
| Upload endpoint (current) | `backend/app/routers/port_calls.py` — `POST /{port_call_id}/documents` |
| ParseWorker | `backend/app/services/parse_worker.py` — `process_email` |
| Worker entry | `backend/app/worker.py` — `process_parse_job` |
| Email model | `backend/app/models/email.py` |
| ParseJob model | `backend/app/models/parse_job.py` |
| Sentinel trigger | `backend/app/services/sentinel_audit_trigger.py` |
| Email list UI | `frontend/src/pages/emails/EmailList.tsx` |
| Port Call Documents UI | `frontend/src/pages/port-calls/PortCallDocuments.tsx` |

---

## Dependencies

- Task 14.10 — Manual document upload & audit trigger (current implementation to refactor)
- Epic 2 — ParseWorker, parse job queue
- Epic 14 — Sentinel audit trigger, AuditEngine

---

## Why this matters

| Concern | Impact |
|---------|--------|
| **Data integrity** | Accurate Sentinel audit requires correct source context (upload date vs email date). |
| **Client trust** | Sensitive documents belong in a "Documents" section, not mixed with email. |
| **Scalability** | Future sources (e.g. Port Authority API) can plug in without breaking Email logic. |
