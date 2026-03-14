# Task 12.3 — Leakage Audit Trigger & Worker

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Integrate the leakage audit into the ARQ background worker flow. Trigger audit when an email containing a financial document is processed; fetch PortCall and Vessel context; invoke AuditService.

---

## Scope

### 1. Trigger condition

- After parse job completes successfully for an email with financial document (e.g. invoice).
- Detect financial document type from `ai_raw_output` or parse job metadata.

### 2. Context retrieval

- Fetch PortCall record (ATA, ATD, Berthing time) linked to Email or parse result.
- Fetch Vessel dimensions (GT, LOA) from linked Vessel.

### 3. Worker integration

- Enqueue leakage audit job (or run inline after parse) with `email_id`, `tenant_id`.
- Worker loads Email, PortCall, Vessel; calls AuditService.
- Persist Anomaly records; update Email/DA with audit status if needed.

### 4. Idempotency

- Same `email_id` should not run audit twice; use idempotency key.

### 5. Feature gate (premium)

- Skip audit for Starter plans; only run for Professional/Enterprise. Check tenant plan via limits/feature service before invoking AuditService.

---

## Acceptance criteria

- [ ] Leakage audit triggers when financial document email is processed.
- [ ] PortCall and Vessel context fetched correctly.
- [ ] AuditService invoked; anomalies persisted.
- [ ] Idempotency prevents duplicate audits for same email.

---

## Related code

- `backend/app/workers/` — ARQ worker, parse job handler
- `backend/app/services/audit_service.py` — AuditService
- Epic 2 — Parse worker, Email entity

---

## Dependencies

- Task 12.2 — AuditService
- Epic 2 — ARQ worker, parse flow
