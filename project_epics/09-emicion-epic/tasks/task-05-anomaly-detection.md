# Task 9.5 — Anomaly Detection (AI Auditor)

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Implement anomaly detection that flags emission reports where (1) consumption is physically impossible for the distance covered, or (2) fuel types mentioned do not match the vessel's technical profile. Goal: prevent submission of fraudulent or erroneous data to authorities.

---

## Scope

### Rule 1: Consumption vs distance

- **Logic:** For "at sea" segments, estimate expected consumption range (e.g. based on typical SFC — Specific Fuel Consumption — or industry benchmarks).
- **Flag:** If reported consumption is outside plausible range (e.g. >2× or <0.2× expected), mark as anomaly.
- **Simplification:** Use rough rule: consumption (MT) / distance (NM) in typical band (e.g. 0.01–0.1 for large vessels); flag outliers.

### Rule 2: Fuel type vs vessel profile

- **Logic:** If vessel has a technical profile with allowed fuel types, check that reported fuel types are in that set.
- **Flag:** Unknown or mismatched fuel type → anomaly.
- **Fallback:** If no profile exists, skip this rule (or warn "no profile").

### Output

- **Anomaly flags:** List of `{ rule, description, severity }` attached to EmissionReport.
- **Status:** `verified | flagged | failed` — reports with anomalies are `flagged`; user can override or correct.

---

## Acceptance criteria

- [ ] Consumption/distance anomaly is detected and flagged.
- [ ] Fuel type mismatch (when vessel profile exists) is detected and flagged.
- [ ] Flagged reports are distinguishable in API and UI; user can review and override.

---

## Related code

- `backend/app/services/emission_anomaly.py` — anomaly rules
- `backend/app/models/emission_report.py` — anomaly_flags, status

---

## Dependencies

- Task 9.1 (EmissionReport model).
- Vessel technical profile (optional; may need to add fuel_types to vessel or separate table).
