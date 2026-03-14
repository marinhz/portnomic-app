# Task 12.2 — AuditService & Detection Rules

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Implement the AuditService that performs comparison logic between AI-extracted invoice data (`ai_raw_output`) and PortCall/operational state. Apply detection rules LD-001 through LD-004 and persist anomalies.

---

## Scope

### 1. AuditService

- **Input:** Email record (with `ai_raw_output`), PortCall, Vessel, optional DA.
- **Output:** List of Anomaly records; persist to DB.
- **Dependencies:** Tenant LLM config (BYOAI) for extraction/validation prompts.

### 2. Detection rules

| Rule ID | Logic | Data required |
|---------|-------|---------------|
| LD-001 | Temporal validation — invoice service date vs. vessel stay (ATA/ATD) | PortCall.ata, PortCall.atd, line item date |
| LD-002 | Duplicate detection — identical service/amount in same PortCall | DA line_items, existing DA entities |
| LD-003 | Tariff shift audit — "Weekend/Holiday" rate when service was standard hours | PortCall events, line item timestamp |
| LD-004 | Quantity variance — invoiced tug/pilot hours vs. Noon Reports | ai_raw_output, Noon Report data |

### 3. LLM prompts (versioned)

- **Extraction prompt:** Extract structured line items (Service, Quantity, Unit Price, Date/Time) from invoice.
- **Validation prompt:** Compare extracted timestamps against AuditLog and PortCall events; return pass/fail per rule.

### 4. AuditLog integration

- Log each AI-driven audit decision (rule_id, result, timestamp) to AuditLog for accountability.

---

## Acceptance criteria

- [ ] AuditService accepts Email + PortCall + Vessel; returns/persists Anomaly list.
- [ ] LD-001 through LD-004 implemented; anomalies have correct rule_id and severity.
- [ ] LLM prompts versioned; tenant LLM key used via BYOAI routing.
- [ ] Audit decisions logged to AuditLog.

---

## Related code

- `backend/app/services/` — AuditService
- `backend/app/prompts/` or equivalent — extraction/validation prompts
- Epic 10 — Tenant LLM config, tenant-aware LLM client

---

## Dependencies

- Task 12.1 — Anomaly table
- Epic 2 — LLM client, ai_raw_output
- Epic 10 — Tenant-aware LLM routing
