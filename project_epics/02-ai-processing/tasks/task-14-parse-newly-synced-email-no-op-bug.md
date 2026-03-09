# Task 2.14 — Bug: Parse does nothing when triggered on newly synced email

**Epic:** [02-ai-processing](../epic.md)

**Type:** Bug

---

## Agent

Use the **AI pipeline** agent ([`.agents/ai-pipeline.md`](../../../.agents/ai-pipeline.md)) with **fastapi-python** and **react-dev** skills. This bug spans ingest, parse API, job queue, worker, and frontend polling — the AI pipeline agent owns the parse flow end-to-end.

---

## Objective

Fix the bug where the user triggers parse on a newly synced email, the request is sent, but nothing happens — no parsing occurs and no result is shown.

## Problem statement

- User receives a new email from sync (e.g. Gmail/Outlook OAuth sync or IMAP poll).
- User opens the email.
- User triggers parse (e.g. "Parse with AI" button).
- **Expected:** Parse job runs, status is shown, and parsed result is displayed when complete.
- **Actual:** Request is sent but nothing happens — no parse runs, no status update, no result. User sees no feedback or change.

## Scope

- **Root cause analysis:** Identify why parse fails or appears to do nothing when triggered on a newly synced email.
- **Possible causes:**
  - **Race condition:** User opens and parses before email is fully persisted or committed; parse request uses stale or invalid `email_id`.
  - **Backend:** Parse job is never enqueued or fails silently for newly synced emails (e.g. wrong tenant context, missing fields).
  - **Frontend:** Request succeeds (202) but polling/subscription never starts or uses wrong `job_id`; success handler does not run.
  - **Email state:** Newly synced email may have different `processing_status` or metadata that causes parse to be skipped or rejected.
  - **Sync vs ingest:** Email from OAuth/IMAP sync may follow a different ingest path than webhook; idempotency or duplicate handling could block parse.
- **Fix:** Ensure parse works reliably when triggered immediately after opening a newly synced email.
- **Logging:** Add or verify logs to trace request flow, job enqueue, and frontend polling for this scenario.

## Root cause (documented)

- **Race condition:** The API pushed the parse job to Redis *before* committing the DB transaction. The worker (running in a separate process) could `blpop` the job immediately, then load `ParseJob` by id — but the job did not exist yet (API hadn't committed). The worker logged "ParseJob X not found", returned silently, and the job was consumed from the queue. The API then committed; the job existed in DB but was never processed. Frontend polling saw status "pending" forever.
- **Fix:** Commit the DB transaction before pushing to Redis in `POST /ai/parse` and `POST /emissions/parse`. Added `await db.commit()` before `redis_client.rpush()` in both routers.

## Acceptance criteria

- [ ] Root cause documented.
- [ ] User can open a newly synced email and trigger parse; parse runs and result is shown.
- [ ] No silent failure — if parse fails, user sees clear error state.
- [ ] Works regardless of timing (immediate parse after sync vs. opening later).

## Related code

- `frontend/src/pages/emails/` — EmailDetail, parse trigger, polling
- `frontend/src/` — Parse status polling, success/error handlers
- Backend: parse API (`POST /ai/parse`), job queue, worker
- [Task 2.12](task-12-frontend-parse-trigger-status.md) — Frontend parse trigger and status
- [Task 2.13](task-13-parse-success-redirect-404-bug.md) — Parse success redirect bug
- Epic 6 (Email Connection) — Sync flow, email ingest from OAuth/IMAP

---

## Dependencies

- Task 2.12 (Frontend parse trigger and status).
- Epic 6 email sync (for reproducing with newly synced emails).
