# Task 2.11 — POST /ai/parse and GET /ai/parse/{job_id} API

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Expose API to submit email for parsing and poll job status/result with proper auth and RBAC (EDD §7.2).

## Scope

- **POST /ai/parse** — Body: email_id (or inline email payload); enqueue job; return job_id or 202 Accepted.
- **GET /ai/parse/{job_id}** — Return status (pending|processing|completed|failed) and result (if completed) or error reason (if failed).
- Auth: JWT required; permission ai:parse; tenant from JWT; only allow jobs for same tenant.
- Job store: persist job_id → email_id, tenant_id, status, result/error; update when worker completes.

## Acceptance criteria

- [ ] Client can submit email for parse and receive job_id; can poll until completed/failed.
- [ ] Only tenant's own jobs are visible; 403 for other tenants' job_ids.
- [ ] Response includes status and (when done) parsed result or error message.
