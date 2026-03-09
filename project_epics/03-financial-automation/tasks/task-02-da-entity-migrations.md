# Task 3.2 — DisbursementAccount entity and migrations

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Add DisbursementAccount (DA) entity and workflow states in DB; Alembic migration (EDD §5.1, §9.2).

## Scope

- **DA:** id, tenant_id, port_call_id, version, type (proforma|final), status (draft|pending_approval|approved|sent), line_items (JSON or relation), totals, pdf_blob_id (nullable), created_at, approved_at, sent_at.
- Indexes: (tenant_id, port_call_id), (tenant_id, status), (tenant_id, created_at).
- Workflow: draft → pending_approval → approved → sent (EDD §9.2).

## Acceptance criteria

- [ ] DA table created with all fields; line_items and totals support JSON or normalized structure.
- [ ] Status transitions are enforceable in service layer; approved_at and sent_at set on transition.
- [ ] Tenant and port_call scoping enforced in all DA queries.
