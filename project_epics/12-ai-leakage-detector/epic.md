# Epic 12 — AI Leakage Detector (Automated Expense Audit)

**Source:** [docs/ai-Leakage-detector.md](../../docs/ai-Leakage-detector.md)  
**Duration (estimate):** 4–5 weeks

---

## Agent assignments

| Task | Agent | Skills |
|------|-------|--------|
| 12.1 Anomaly table & schema | Backend | fastapi-python, python-project-structure |
| 12.2 AuditService & detection rules | Backend | fastapi-python, python-project-structure |
| 12.3 Leakage audit trigger & worker | Backend | fastapi-python |
| 12.4 Circuit breaker & pending manual review | Backend | fastapi-python |
| 12.5 Discrepancy UI (DA workspace) | Frontend | react-dev, react-router-v7, tailwind-design-system |
| 12.6 High-risk invoice toast alerts | Frontend | react-dev, tailwind-design-system |
| 12.7 Sidebar icon & feature gating (Starter: icon only) | Frontend | react-dev, tailwind-design-system |
| 12.8 DA List: Leakage Detector filter & icon | Frontend | react-dev, tailwind-design-system |

---

## Strategic objective

Automatically cross-reference incoming vendor invoices (DA line items) against actual operational data (Port Call logs) to identify overbilling, duplicate charges, or tariff misapplications. Uses tenant-configured LLM (BYOAI) for extraction and validation; zero infrastructure overhead for the platform.

---

## Scope

### Trigger & ingestion

- **Source:** Module triggers when an email containing a financial document is processed by the ARQ background worker.
- **Context retrieval:** Fetch corresponding PortCall record (ATA, ATD, Berthing time) and Vessel dimensions (GT, LOA).

### Dual-prompt processing (BYOAI)

- **Extraction:** AI extracts structured line items from the invoice (Service, Quantity, Unit Price, Date/Time of service).
- **Validation:** AI compares extracted service timestamps against AuditLog and PortCall operational events.

### Detection rules (audit logic)

| Rule ID | Detection logic | Data points required |
|---------|-----------------|----------------------|
| LD-001 | Temporal validation | Invoice service date vs. vessel stay (ATA/ATD) |
| LD-002 | Duplicate detection | DA entity: identical service descriptions/amounts in same PortCall |
| LD-003 | Tariff shift audit | Flags "Weekend/Holiday" rates if service occurred during standard hours |
| LD-004 | Quantity variance | Invoiced tug/pilot hours vs. AI-parsed Noon Reports |

### Backend

- **AuditService:** Comparison logic between `ai_raw_output` and PortCall state.
- **Anomaly persistence:** Detected discrepancies stored in Anomaly table linked to Email and DA entities.
- **Circuit breaker:** LLM failures do not halt core ingestion; invoice marked "Pending Manual Review" on audit failure.

### Frontend

- **Status indicators:** Sonner toasts for "High Risk" invoices upon parsing.
- **Discrepancy UI:** Side-by-side view in DA Workspace: "Invoiced Value" vs. "System Expected Value".
- **Highlighting:** Visual flags on line items that failed audit logic.

### Feature gating (premium module)

- **Premium only:** Full access (audit, discrepancy UI, toasts) for Professional and Enterprise plans.
- **Starter plans:** Can only view the Leakage Detector icon in the sidebar — teaser/disabled; click shows upgrade CTA.

### Security & privacy (BYOAI)

- **API key routing:** Use `tenant_id` to retrieve encrypted LLM key from Tenant LLM config.
- **Audit transparency:** All AI-driven audit decisions logged in append-only AuditLog.

---

## Out of scope (for this epic)

- Usage metering per tenant (token counts).
- Custom detection rules per tenant (future enhancement).
- Automated dispute/claim workflows (manual review only).

---

## Acceptance criteria

- [ ] Leakage audit triggers when financial document email is processed by ARQ worker.
- [ ] AuditService runs LD-001 through LD-004; anomalies persisted to Anomaly table.
- [ ] LLM failures trigger circuit breaker; invoice marked "Pending Manual Review".
- [ ] DA Workspace shows side-by-side discrepancy view and visual flags on failed line items.
- [ ] High-risk invoices trigger Sonner toast alerts upon parsing.
- [ ] All audit decisions logged in AuditLog; tenant LLM key used via BYOAI routing.
- [ ] Starter plans see Leakage Detector icon in sidebar only (disabled); click shows upgrade CTA. Professional/Enterprise get full access.

---

## Dependencies

- Epic 2 (AI processing) — ARQ worker, parse job, LLM client, Email entity.
- Epic 3 (Financial automation) — DA entity, PortCall, line items.
- Epic 8 (Business & monetization) — Plan tiers, feature gating, limits service.
- Epic 10 (BYOAI) — Tenant LLM config, API key routing, tenant-aware LLM client.

---

## Business value

| Aspect | Benefit |
|--------|---------|
| **Zero infrastructure** | Client's own AI key does the work; no platform spend. |
| **Immediate ROI** | Actively saves money by catching human error or vendor overcharging. |
| **Data synergy** | Utilizes vessel data, email parsing, financial workflows, and audit logs. |
| **Investor appeal** | "Killer feature" — doesn't just manage data; it audits and protects revenue. |
