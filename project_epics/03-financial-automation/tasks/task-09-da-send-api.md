# Task 3.9 — POST /da/{id}/send API

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Trigger PDF generation and email dispatch for an approved DA; return job id or 202 until complete (EDD §7.2).

## Scope

- **POST /da/{id}/send** — DA must be in status approved; enqueue job(s): PDF generation then email send (or combined worker); return 202 with job_id or wait for sync completion per design.
- Permission: da:send; tenant-scoped.
- If async: client can poll job status; on success DA is sent (status, sent_at, audit).
- 400 if DA not approved; 404 if DA not found or wrong tenant.

## Acceptance criteria

- [ ] Only approved DAs can be sent; unauthorized or wrong state return 4xx.
- [ ] Sending triggers PDF + email flow; DA is updated and audited when complete.
- [ ] Client receives clear success or job reference for async flow.
