# Task 3.10 — DA workspace frontend

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

View Proforma/Final DA, approve, PDF preview, and send from the UI (EDD §4.1).

## Scope

- **DA view:** Display DA (line items, totals, status); show PDF preview when pdf_blob_id exists (embed or link).
- **Actions:** Approve (when permitted and in draft/pending_approval); Send (when approved).
- **Generate:** From port call or dashboard, trigger generate (proforma/final); navigate to new DA.
- Links from dashboard and port call detail to DA list and to generate.
- Permission-based visibility: approve/send buttons only when user has da:approve / da:send.

## Acceptance criteria

- [ ] User can open DA, see line items and totals, and (if allowed) approve and send.
- [ ] PDF preview loads when available; send triggers backend and reflects sent state.
- [ ] Generate flow creates DA and opens it in workspace; errors shown clearly.
