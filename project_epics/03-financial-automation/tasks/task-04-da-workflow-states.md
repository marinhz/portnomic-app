# Task 3.4 — DA workflow states and transitions

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Enforce DA workflow: draft → pending_approval → approved → sent; only valid transitions allowed; audit on approve (EDD §9.2, §9.3).

## Scope

- State machine: draft (editable); optional pending_approval; approved (ready to send); sent (immutable).
- Transitions: submit for approval (draft → pending_approval); approve (→ approved); send (→ sent).
- Approve action: permission da:approve; record approved_at and user in audit log (EDD §9.3).
- Sent state: no further edits; pdf_blob_id and sent_at set when send completes.

## Acceptance criteria

- [ ] Invalid transitions return 400 or 403 with clear message.
- [ ] Approve is permission-gated and audited; sent DAs are immutable.
- [ ] UI and API reflect current status and allowed actions.
