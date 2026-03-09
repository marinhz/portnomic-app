# Task 3.6 — POST /da/{id}/approve API

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Approve a DA (transition to approved); permission-gated and audited (EDD §7.2, §9.3).

## Scope

- **POST /da/{id}/approve** — Valid only when DA status is draft or pending_approval; transition to approved; set approved_at; record in audit log (user, timestamp, DA id).
- Permission: da:approve; tenant-scoped.
- Return updated DA or 400 if invalid state.

## Acceptance criteria

- [ ] Only authorized users can approve; DA must be in approvable state.
- [ ] approved_at and audit log entry created; DA status = approved.
- [ ] Idempotent for already-approved DA (return success or 400 as designed).
