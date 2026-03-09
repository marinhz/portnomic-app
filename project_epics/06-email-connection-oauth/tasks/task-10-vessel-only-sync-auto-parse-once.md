# Task 6.10 — Vessel-only email sync with auto-parse once and manual retry

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

1. Sync only **vessel-related** emails (not all inbox emails).
2. On ingest: **automatically parse once** (single attempt, no retries).
3. Allow user to **manually retry parse** from the UI when desired.

---

## Problem statement

- Current sync ingests all emails from connected mailboxes (Gmail, Outlook, IMAP).
- Many emails are unrelated to maritime operations (marketing, personal, etc.).
- Parse worker retries on transient errors, which may be unnecessary for initial ingest.
- User has no clear way to retry parsing when auto-parse fails.

---

## Scope

### 1. Vessel-related filter (sync-time)

- **Filter criteria:** Only ingest emails that appear vessel-related. Options (implement one or combine):
  - **Option A (tenant vessels):** Match subject/body against tenant's vessel names and IMO numbers from `vessels` table.
  - **Option B (heuristic keywords):** Match subject/body against maritime keywords (e.g. `ETA`, `ETD`, `port call`, `disbursement`, `vessel`, `IMO`, `arrival`, `departure`, port names).
  - **Option C (hybrid):** Tenant vessels + heuristic fallback; if tenant has no vessels, use heuristic only.
- **Config:** Allow tenant admin to toggle "strict vessel-only" vs "all emails" (e.g. per mail_connection or tenant setting) for backward compatibility.
- **Implementation:** Apply filter in `oauth_ingest.ingest_and_enqueue` (or equivalent) before persisting; skip non-matching emails without storing.
- **Logging:** Log skipped emails count and reason (e.g. `Skipped N non-vessel-related emails`).

### 2. Auto-parse once (single attempt)

- **Behavior:** When an email is ingested, enqueue parse job with **single attempt** flag.
- **No retries:** If parse fails (LLM error, timeout, etc.), do not retry; mark job as `failed` and optionally email `processing_status="failed"`.
- **Implementation:** Add `single_attempt: bool` (or similar) to job payload or ParseJob; worker respects it and skips retries.
- **Config:** Consider `LLM_PARSE_SINGLE_ATTEMPT_ON_INGEST=true` or similar.

### 3. Manual retry

- **UI:** "Parse with AI" or "Retry parse" button on email detail/list (see [Task 2.12](../../02-ai-processing/tasks/task-12-frontend-parse-trigger-status.md)).
- **API:** `POST /ai/parse` with `email_id` already exists; ensure it creates a new job and allows retries (no single-attempt flag).
- **Behavior:** User can retry manually when auto-parse failed or when they want to re-parse.

---

## Acceptance criteria

- [ ] Sync ingests only vessel-related emails (per filter criteria); non-vessel emails are skipped.
- [ ] Tenant can optionally disable filter (sync all) via settings or config.
- [ ] Logging shows: `Gmail: tenant=... ingested N, skipped M non-vessel-related`.
- [ ] Auto-parse runs once per ingested email; no retries on failure.
- [ ] Failed parse jobs are clearly marked; user can trigger manual retry from UI.
- [ ] Manual retry creates a new parse job and can retry (with normal retry logic if desired).

---

## Related code

- `backend/app/services/oauth_ingest.py` — `_poll_gmail`, `_poll_outlook`, `_poll_tenant_imap`; ingest flow
- `backend/app/services/email_ingest.py` — `ingest_and_enqueue`
- `backend/app/services/parse_worker.py` — `process_email`; retry logic
- `backend/app/worker.py` — `process_parse_job`; `max_retries` handling
- `backend/app/services/vessel.py` — vessel lookup for tenant
- `backend/app/routers/ai.py` — `POST /ai/parse`
- `frontend/src/pages/emails/EmailDetail.tsx` — parse trigger UI

---

## Dependencies

- [Task 6.5](task-05-ingest-from-oauth-mailboxes.md) — Ingest from OAuth mailboxes (worker)
- [Task 2.12](../../02-ai-processing/tasks/task-12-frontend-parse-trigger-status.md) — Frontend parse trigger and status (manual retry)
