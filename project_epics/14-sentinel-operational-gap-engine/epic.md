# Epic 14 — The Sentinel: Operational Gap Engine

**Source:** [docs/sentinel-operational-gap-engine.md](../../docs/sentinel-operational-gap-engine.md)  
**Duration (estimate):** 5–6 weeks

---

## Agent assignments

| Task | Agent | Skills |
|------|-------|--------|
| 14.1 time_overlap logic & core utilities | Backend | fastapi-python, python-project-structure |
| 14.2 TimelineEvent model & normalization | Backend | fastapi-python, python-project-structure |
| 14.3 discrepancies table schema | Backend | fastapi-python |
| 14.4 AuditEngine & Triple-Check rules | Backend | fastapi-python |
| 14.5 AIS integration (aisstream.io) | Backend | fastapi-python |
| 14.6 Sentinel audit trigger & worker | Backend | fastapi-python |
| 14.7 SentinelAlert component | Frontend | react-dev, tailwind-design-system |
| 14.8 SideBySideAudit component | Frontend | react-dev, tailwind-design-system |
| 14.9 Port Call dashboard integration | Frontend | react-dev, react-router-v7, tailwind-design-system |
| 14.10 Manual document upload & audit trigger | Frontend + Backend | react-dev, react-router-v7, tailwind-design-system, fastapi-python |
| 14.11 Document ingestion refactor (separate manual uploads from email) | Frontend + Backend | react-dev, react-router-v7, tailwind-design-system, fastapi-python |

---

## Strategic objective

Create a pro-active validation layer that cross-references four independent data sources (DA, Port Logs/SOF, Noon Reports, AIS) to identify financial leakages and operational discrepancies in real-time. The engine normalizes all sources into a unified `TimelineEvent` model and runs the "Triple-Check" algorithm to flag overcharged service hours, incorrect berthage, and unusual fuel consumption.

---

## Scope

### Data sources & normalization

| Source | Entity | Data |
|--------|--------|------|
| **A (Financial)** | Disbursement Accounts | Extracted line items from DA |
| **B (Operational)** | Statement of Facts (SOF) | Tug fast/off, Pilot on/off timestamps |
| **C (Vessel)** | Noon Reports | Fuel remaining, GPS position, Engine hours |
| **D (External)** | AIS Satellite Data | Actual berth arrival/departure times |

All sources normalize to unified `TimelineEvent` objects for cross-reference.

### Core logic: Triple-Check algorithm

| Rule | Input | Logic | Action |
|------|-------|-------|--------|
| **Rule 1: Temporal Tug/Pilot Audit** | `DA_Tug_Hours` vs. `SOF_Tug_Timestamps` | If `DA_Invoiced_Hours` > (`SOF_Tug_Off` - `SOF_Tug_Fast`) + 0.5hr buffer | Flag **"High Risk: Overcharged Service Hours"** |
| **Rule 2: Berthage/Stay Verification** | `DA_Berth_Fee_Days` vs. `AIS_Berth_Stay_Duration` | Compare invoiced days vs. actual GPS "at berth" status | Flag **"Potential Error: Incorrect Berthage Calculation"** |
| **Rule 3: Fuel Consumption Paradox** | `Noon_Report_Fuel_Consumption` vs. `SOF_Wait_Time` | High fuel consumption while SOF shows "Idle at Anchorage" 12+ hours | Flag **"Operational Alert: Unusual Fuel Burn while Idle"** |

### Developer focus: time_overlap logic

**Priority:** The system must be able to tell if two events claimed to happen at the same time actually did. Implement `time_overlap` logic first as the foundation for all temporal validations.

### Backend

- **AuditEngine:** Inherits from existing worker pattern; method `compare_events(port_call_id)` triggered after AI parsing of new email/file.
- **Output:** `AuditReport` JSON stored in `discrepancies` table, linked to PortCall.
- **AIS:** Integration with aisstream.io for actual berth arrival/departure.

### Database

- **Table:** `discrepancies`
  - `id`, `port_call_id` (FK), `tenant_id`
  - `source_documents`: Array[UUID] (links to conflicting emails/files)
  - `severity`: Enum (Low, Medium, High)
  - `estimated_loss`: Decimal (Euro amount of overcharge)
  - `description`: AI-generated explanation

### Frontend

- **SentinelAlert:** High-visibility card in Port Call dashboard.
- **SideBySideAudit:** Table with "Vendor Claims" (Invoice) | "Operational Reality" (SOF/AIS) | "Variance" (highlighted).

### Security & privacy (BYOAI)

- All audits use `tenant_id`'s specific LLM keys (BYOAI).
- Each audit result logged in immutable `AuditLog`.

---

## Out of scope (for this epic)

- Automated dispute/claim workflows (manual review only).
- Usage metering per tenant (token counts).
- Custom rules per tenant (future enhancement).

---

## Acceptance criteria

- [ ] `time_overlap` utility correctly determines if two events claimed at same time actually overlap.
- [ ] TimelineEvent model normalizes DA, SOF, Noon Report, and AIS data.
- [ ] AuditEngine runs Rule 1, 2, 3; persists to `discrepancies` table.
- [ ] AIS integration (aisstream.io) provides berth arrival/departure for berthage verification.
- [ ] Audit triggers after parse job; `compare_events(port_call_id)` produces AuditReport.
- [ ] SentinelAlert and SideBySideAudit components visible in Port Call dashboard.
- [ ] All audit decisions logged in AuditLog; tenant LLM key used via BYOAI.

---

## Dependencies

- Epic 2 (AI processing) — ARQ worker, parse job, LLM client, Email entity.
- Epic 3 (Financial automation) — DA entity, PortCall, line items.
- Epic 9 (Emissions) — Noon Report / Emission data for fuel consumption.
- Epic 10 (BYOAI) — Tenant LLM config, API key routing.
- Epic 12 (AI Leakage Detector) — Anomaly/AuditService patterns (complementary; Sentinel adds AIS + SOF + Noon cross-reference).

---

## Business value

| Aspect | Benefit |
|--------|---------|
| **Four-source validation** | DA + SOF + Noon + AIS = comprehensive operational truth. |
| **Pro-active detection** | Catches overcharges and discrepancies before approval. |
| **Time-overlap accuracy** | Foundation for temporal audit; reduces false positives. |
| **External verification** | AIS provides independent berth timing; vendor claims vs. satellite truth. |
