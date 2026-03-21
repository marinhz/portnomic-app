# Task 14.10 — Manual Document Upload & Audit Trigger

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Frontend** and **Backend** agents with **react-dev**, **react-router-v7**, **tailwind-design-system**, and **fastapi-python** skills.

---

## Context

Current system only ingests files via Email Worker. This task adds a manual UI upload path to allow users to audit historical files or test "The Sentinel" logic directly. It introduces the **Interactive Layer** needed for Business Intelligence and manual auditing.

---

## Objective

Implement a manual document upload flow at the Port Call documents page. Once a file is uploaded, trigger immediate AI parsing (bypassing the email queue), run the Sentinel AuditEngine on the newly parsed data, and surface results in real time.

---

## Scope

### 1. UI — Documents page & FileUploader

- **Location:** `/dashboard/port-calls/[id]/documents`
- **Component:** `FileUploader` (Drag & Drop).
- **Supported Formats:** PDF, XLSX, JPG (scanned invoices).
- **Document Categorization:** User must label each file as one of:
  - `Statement of Facts (SOF)`
  - `Disbursement Account (DA/Invoice)`
  - `Noon Report`
- Route: React Router v7 loader for port call + documents list; `FileUploader` in documents tab/section.

### 2. Backend — Manual upload API

- **Endpoint:** `POST /api/port-calls/{id}/documents` (or equivalent).
- **Payload:** Multipart form with `file` + `category` (enum: SOF, DA, NOON_REPORT).
- **Flow:**
  1. Validate file type (PDF, XLSX, JPG).
  2. Store file; create document/email record linked to PortCall.
  3. **Immediate ParseWorker trigger:** Enqueue parse job directly (bypass email queue).
  4. **Sentinel execution:** After parse completes, trigger `AuditEngine.compare_events(port_call_id)`.
  5. Return job/audit ID for status polling or WebSocket subscription.

### 3. Workflow logic (The Trigger)

1. **Immediate AI Parsing:** Trigger `ParseWorker` immediately on upload (no email ingestion).
2. **Sentinel Execution:** After parsing, automatically run `AuditEngine` to compare the new file with existing documents in that PortCall.
3. **Real-time Update:** Use WebSockets or polling to show "Audit in progress..." and then display results (e.g. SentinelAlert, SideBySideAudit).

### 4. Status & results display

- Show "Uploading...", "Parsing...", "Auditing..." states.
- On completion: refresh discrepancies; show SentinelAlert if discrepancies exist.
- Handle errors: invalid file, parse failure, audit failure.

---

## Acceptance criteria

- [ ] Route `/dashboard/port-calls/[id]/documents` exists with FileUploader.
- [ ] User can drag-and-drop or select PDF, XLSX, JPG.
- [ ] User must select document category (SOF, DA, Noon Report) before/during upload.
- [ ] `POST /api/port-calls/{id}/documents` accepts file + category; triggers ParseWorker.
- [ ] ParseWorker completion triggers AuditEngine for that PortCall.
- [ ] UI shows "Audit in progress..." and updates when complete.
- [ ] Results visible via SentinelAlert / SideBySideAudit when discrepancies exist.

---

## Related code

- `frontend/src/routes/` — Port Call routes, documents sub-route
- `frontend/src/components/` — FileUploader
- `backend/app/worker.py` — ARQ worker, ParseWorker
- `backend/app/services/sentinel/audit_engine.py` — AuditEngine
- Epic 2 — AI parse API, parse flow

---

## Dependencies

- Task 14.4 — AuditEngine & Triple-Check rules
- Task 14.6 — Sentinel audit trigger (extend to support manual trigger path)
- Task 14.7 — SentinelAlert
- Task 14.8 — SideBySideAudit
- Epic 2 — ParseWorker, parse job
- Epic 3 — PortCall, document storage
