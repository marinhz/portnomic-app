# Task 14.4 — AuditEngine & Triple-Check Rules

**Epic:** [14-sentinel-operational-gap-engine](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Implement the AuditEngine that runs the Triple-Check algorithm (Rules 1–3) using normalized TimelineEvents, time_overlap logic, and persisted Discrepancy records.

---

## Scope

### 1. AuditEngine class

- **Method:** `compare_events(port_call_id: UUID) -> AuditReport`
- **Input:** Port call ID; fetches all TimelineEvents via `get_timeline_events`.
- **Output:** AuditReport (list of Discrepancy records, summary counts).
- **Dependencies:** Tenant LLM config (BYOAI) for AI-generated descriptions where needed.

### 2. Rule implementations

| Rule ID | Name | Logic |
|---------|------|-------|
| **S-001** | Temporal Tug/Pilot Audit | `DA_Invoiced_Hours` vs. `SOF_Tug_Off - SOF_Tug_Fast`; flag if DA > SOF + 0.5hr buffer |
| **S-002** | Berthage/Stay Verification | `DA_Berth_Fee_Days` vs. `AIS_Berth_Stay_Duration`; flag mismatch |
| **S-003** | Fuel Consumption Paradox | High Noon fuel consumption + SOF "Idle at Anchorage" 12+ hrs |

### 3. time_overlap integration

- Rule S-001: Use `time_overlap` to validate if invoiced tug/pilot window overlaps with SOF timestamps; flag overcharge when invoiced > actual + buffer.
- Rule S-002: Compare day counts; AIS provides actual berth duration.
- Rule S-003: Cross-reference fuel events with idle events.

### 4. AuditLog integration

- Log each Sentinel audit run (port_call_id, rules executed, discrepancy count) to AuditLog.

---

## Acceptance criteria

- [ ] AuditEngine.compare_events(port_call_id) returns AuditReport with Discrepancy list.
- [ ] S-001, S-002, S-003 implemented; Discrepancy records have correct rule_id and severity.
- [ ] time_overlap used for S-001 temporal validation.
- [ ] Discrepancies persisted to `discrepancies` table.
- [ ] Audit run logged to AuditLog.

---

## Related code

- `backend/app/services/sentinel/audit_engine.py`
- `backend/app/services/sentinel/time_overlap.py` — Task 14.1
- `backend/app/services/sentinel/timeline_events.py` — Task 14.2
- Epic 10 — Tenant LLM config (BYOAI)

---

## Dependencies

- Task 14.1 — time_overlap
- Task 14.2 — TimelineEvent, get_timeline_events
- Task 14.3 — Discrepancy model
- Task 14.5 — AIS data for S-002 (or stub)
