# Epic 3 — Financial Automation

**Source:** SHIPFLOW_AI_Engineering_Design_Document.md, Implementation Roadmap Phase 3  
**Duration (estimate):** 3 weeks

---

## Objective

Deliver end-to-end financial workflow: store and version port-specific tariffs, generate Proforma and Final Disbursement Accounts (DA) via a formula engine, produce PDFs, and support approval workflow and email dispatch.

---

## Scope

### Tariffs

- **Tariff** entity: tenant_id, port_id, name, version, formula_config (JSON), valid_from, valid_to (EDD §5.1).
- **Store and version** port-specific tariff configurations; formula or table-driven (e.g. per-call fees, per-ton fees) (EDD §9.1).

### DA formula engine

- **Inputs:** Port call, vessel, port, tariff (versioned), optional AI-parsed line items (EDD §9.1).
- **Output:** Line items (description, quantity, unit price, amount, currency); subtotals and totals (EDD §9.1).
- **Versioning:** Tariff and DA version stored; history retained for audit (EDD §9.1).

### DA entity and workflow

- **DisbursementAccount:** tenant_id, port_call_id, version, type (proforma|final), status (draft|pending_approval|approved|sent), line_items, totals, pdf_blob_id, created_at, approved_at, sent_at (EDD §5.1).
- **States:** Draft → Pending approval (optional) → Approved → Sent (EDD §9.2).
- **Approval:** Authorized user approves; action audited (EDD §9.3).

### PDF and dispatch

- **PDF:** Template (e.g. HTML → PDF) with DA data and branding; store in object storage; link in DA record (EDD §9.3, §7.4).
- **Email:** To addresses from port call or tenant config; attachment PDF; body from template; SMTP or transactional API (EDD §9.3, §7.4).
- **Background:** PDF generation and email send run in workers; API triggers jobs (EDD §4.2).

### API

- **POST /da/generate** — Generate Proforma or Final DA for port call (body: port_call_id, type) (EDD §7.2).
- **GET /da/{id}** — Get DA (JWT, da:read).
- **POST /da/{id}/approve** — Approve DA (JWT, da:approve).
- **POST /da/{id}/send** — Send DA (PDF + email) (JWT, da:send).

### Frontend

- **DA workspace:** View Proforma/Final DA, approve, PDF preview, send (EDD §4.1).
- Dashboard/port call views link to DA list and generation.

---

## Out of scope

- Email ingest and AI parsing (Epic 2).
- Penetration testing and GDPR tooling (Epic 4).

---

## Acceptance criteria

- [ ] Tariffs are stored and versioned per port; formula engine produces line items and totals from port call + tariff + optional AI data.
- [ ] Proforma and Final DA can be generated; DA has correct workflow states and audit on state changes.
- [ ] Approve action is permission-gated and logged; Send triggers PDF generation and email dispatch.
- [ ] PDF is generated in a worker, stored in object storage, and linked to DA; email is sent with PDF attachment.
- [ ] API supports generate, get, approve, and send with correct RBAC; frontend supports full DA workflow and PDF preview.

---

## EDD references

- §5.1 Tariff, DisbursementAccount; §5.2 relationships  
- §7.2 /da/* endpoints; §7.4 PDF and email integration  
- §9 DA generator & financial workflow (formula engine, workflow states, PDF & dispatch)
