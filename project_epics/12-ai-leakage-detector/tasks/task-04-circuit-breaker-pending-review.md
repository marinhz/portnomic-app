# Task 12.4 — Circuit Breaker & Pending Manual Review

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Ensure LLM failures do not halt the core ingestion flow. If the leakage audit fails (LLM timeout, API error, etc.), mark the invoice as "Pending Manual Review" and allow operators to proceed.

---

## Scope

### 1. Circuit breaker behavior

- Wrap AuditService call in try/except; catch LLM/network errors.
- On failure: do not retry audit in same job; mark Email or DA with `audit_status = pending_manual_review`.
- Core parse/ingestion flow continues; invoice data is still persisted.

### 2. Status field

- Add `audit_status` to Email or DA: `completed`, `pending_manual_review`, `failed`.
- Default `completed` when audit succeeds; `pending_manual_review` when audit fails.

### 3. Logging & alerting

- Log audit failure reason (e.g. LLM timeout, invalid response).
- Optional: emit metric or event for monitoring (e.g. audit_failure_count).

---

## Acceptance criteria

- [ ] LLM failure in audit does not block parse/ingestion.
- [ ] Invoice marked "Pending Manual Review" when audit fails.
- [ ] Failure reason logged; operator can manually review and override.

---

## Related code

- `backend/app/workers/` — audit job handler
- `backend/app/models/` — Email or DA audit_status field
- `backend/alembic/versions/` — migration for audit_status

---

## Dependencies

- Task 12.3 — Leakage audit trigger & worker
