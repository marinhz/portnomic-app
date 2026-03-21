# Data Specification: "The Sentinel" Test Suite

**Objective:** Create 3 documents for a single Port Call (Vessel: MV Portnomic Voyager, Port: Rotterdam) with intentional discrepancies to verify the AI's detection logic.

---

## Port Call Context (Required Baseline)

The Port Call must exist with these values for S-002 (Berthage) to use eta/etd as the "actual stay" stub:

| Field | Value | Notes |
|-------|-------|-------|
| **Vessel** | MV Portnomic Voyager | Any valid vessel linked to port call |
| **Port** | Rotterdam (ECT Delta Terminal) | Any port record |
| **ETA** | 2026-03-15 09:00 UTC | First Line Ashore = 10:00 LT (Rotterdam CET = UTC+1) |
| **ETD** | 2026-03-16 13:00 UTC | Unberthed = 14:00 LT |
| **Actual stay** | ~28 hours (1.17 days) | Used by S-002 when AIS unavailable |

---

## Document 1: Statement of Facts (SOF)

**Source:** Operational truth from Port/Terminal.  
**Storage:** `Email.ai_raw_output` with key `sof_timestamps` or `port_log`.  
**Normalizer:** `sof_normalizer.normalize_sof()`

### Required Fields (ai_raw_output structure)

```json
{
  "sof_timestamps": {
    "tug_fast": "2026-03-15T07:30:00Z",
    "tug_off": "2026-03-15T08:30:00Z",
    "pilot_on": "2026-03-15T08:00:00Z",
    "pilot_off": "2026-03-15T09:00:00Z"
  }
}
```

### Field Mapping

| Spec Field | Normalizer Expectation | Value |
|------------|------------------------|-------|
| Tug 1 (Fairplay-21) Fast | `tug_fast` (ISO 8601) | 08:30 LT → 07:30 UTC |
| Tug 1 (Fairplay-21) Cast off | `tug_off` (ISO 8601) | 09:30 LT → 08:30 UTC |
| **Total actual tug work** | Computed: `tug_off - tug_fast` | **1.0 hour** |
| Pilot on/off | `pilot_on`, `pilot_off` | Optional; include for pilot audit (match DA) |

### Notes for Physical Documents (PDF/XLSX)

If creating a real SOF PDF or spreadsheet for upload/OCR, ensure the text contains:
- "Tug Fast: 08:30" and "Cast off: 09:30" on 15 March 2026
- Vessel name: MV Portnomic Voyager
- Port: Rotterdam / ECT Delta Terminal
- Arrival: 10:00 (First Line Ashore)
- Departure: 14:00 (Unberthed) on 16 March

---

## Document 2: Final Disbursement Account (DA / Invoice)

**Source:** Financial claim from Agent.  
**Storage:** `DisbursementAccount.line_items` (JSONB).  
**Normalizer:** `da_normalizer.normalize_da_line_items()`

### Required Line Items (intentional overcharges)

```json
{
  "line_items": [
    {
      "description": "Tugboat charges",
      "quantity": 3.0,
      "amount": 2550,
      "service_date": "2026-03-15T07:30:00Z"
    },
    {
      "description": "Berthage / Quay dues",
      "quantity": 3.0,
      "amount": 3300,
      "service_date": "2026-03-15T09:00:00Z"
    },
    {
      "description": "Pilotage fee",
      "quantity": 1.0,
      "amount": 900,
      "service_date": "2026-03-15T08:00:00Z"
    }
  ],
  "totals": {
    "subtotal": 6750,
    "tax": 0,
    "total": 6750,
    "currency": "EUR"
  }
}
```

### Discrepancy Summary

| Item | Invoiced | Actual (SOF/ETA-ETD) | Expected Sentinel |
|------|----------|----------------------|-------------------|
| **Tugboat** | 3.0 h @ €850/hr = €2,550 | 1.0 h (SOF) | **Alert (High):** 2.0 h overbilled → €1,700 overcharge |
| **Berthage** | 3 days @ €1,100/day = €3,300 | ~1.17 days (eta→etd) | **Alert (Medium):** Stay < 2 days, billed 3 days |
| **Pilotage** | €900 (1h) | Matches SOF pilot_on→pilot_off | No alert |

### Keyword Mapping for DA Normalizer

The `da_normalizer` matches line items by `description`:
- **Tug:** `tug`, `towing` → `tug_service`
- **Berthage:** `berth`, `berthage`, `quay`, `wharf`, `mooring` → `berth_fee_days`
- **Pilot:** `pilot`, `pilotage` → `pilot_service`

`service_date` is used for event start; `eta`/`etd` from port call are used when `service_date` is missing (e.g. for berth).

---

## Document 3: Vessel Noon Report (Port Stay)

**Source:** On-board report from Captain.  
**Storage:** `EmissionReport` + `FuelEntry` records.  
**Normalizer:** `noon_report_normalizer.normalize_noon_report()`

### Required Fields

| Field | Value | Notes |
|------|-------|-------|
| **Report type** | Port Stay Report | |
| **Position** | Rotterdam Berth 4 | |
| **Report date** | 2026-03-16 | End of port stay |
| **Arrival fuel (VLSFO)** | 450.5 MT | |
| **Departure fuel (VLSFO)** | 438.0 MT | |
| **Total consumed in port** | 12.5 MT | |

### EmissionReport + FuelEntry Structure

```json
{
  "report_date": "2026-03-16",
  "vessel_id": "<port_call.vessel_id>",
  "port_call_id": "<port_call.id>",
  "fuel_entries": [
    {
      "fuel_type": "VLSFO",
      "consumption_mt": 12.5,
      "operational_status": "at_berth"
    }
  ],
  "distance_nm": null
}
```

### EU ETS CO₂ Calculation (Verification)

- **Formula:** 12.5 MT × 3.114 (VLSFO conversion factor) = **38.9 tCO₂**
- **Operational timestamps:** Must align with SOF (Arrival 10:00, Departure 14:00)

### S-003 Behavior (No Alert Expected)

- **Operational status:** `at_berth` (not `at_anchor`)
- S-003 only fires when `idle_at_anchorage` (SOF) 12+ hrs **and** high fuel consumption
- This port stay has no `idle_at_anchorage` event → **Verification (Success):** Fuel consumption and CO₂ match the operational timeline

---

## Expected Sentinel Output (Test Result)

When these 3 documents are linked to the same Port Call and `AuditEngine.compare_events(port_call_id)` runs:

| Rule | Severity | Description |
|------|----------|-------------|
| **S-001** | High | Tug duration mismatch: DA invoiced 3.0h, SOF actual 1.0h (buffer 0.5h). Overcharged Service Hours. Est. loss: €1,700 |
| **S-002** | Medium | Berthage mismatch: DA claims 3.0 days, actual berth stay ~1.2 days (eta_etd_stub). Incorrect Berthage Calculation |
| **S-003** | — | No finding (fuel at berth, no idle-at-anchorage paradox) |

### Verification Checklist

- [ ] S-001 fires: Tug overcharge (2h overbilled)
- [ ] S-002 fires: Berthage overcharge (3 days billed, ~1.2 days actual)
- [ ] S-003 does not fire: Fuel consumption consistent with berth stay
- [ ] Pilot line item: No discrepancy (matches SOF pilot timestamps)

---

## Fixture / Test Setup (Python)

For pytest or integration tests, use this structure to seed the database:

```python
# Port Call
eta = datetime(2026, 3, 15, 9, 0, 0, tzinfo=timezone.utc)   # 10:00 LT Rotterdam
etd = datetime(2026, 3, 16, 13, 0, 0, tzinfo=timezone.utc)  # 14:00 LT Rotterdam

# Email (SOF)
email.ai_raw_output = {
    "sof_timestamps": {
        "tug_fast": "2026-03-15T07:30:00Z",
        "tug_off": "2026-03-15T08:30:00Z",
        "pilot_on": "2026-03-15T08:00:00Z",
        "pilot_off": "2026-03-15T09:00:00Z",
    }
}

# DisbursementAccount (DA)
da.line_items = [
    {"description": "Tugboat charges", "quantity": 3.0, "amount": 2550, "service_date": "2026-03-15T07:30:00Z"},
    {"description": "Berthage / Quay dues", "quantity": 3.0, "amount": 3300, "service_date": "2026-03-15T09:00:00Z"},
    {"description": "Pilotage fee", "quantity": 1.0, "amount": 900, "service_date": "2026-03-15T08:00:00Z"},
]

# EmissionReport + FuelEntry (Noon Report)
# report_date=2026-03-16, fuel_entries=[{fuel_type: "VLSFO", consumption_mt: 12.5, operational_status: "at_berth"}]
```

---

## Related Code

- `backend/app/services/sentinel/sof_normalizer.py` — SOF → TimelineEvent
- `backend/app/services/sentinel/da_normalizer.py` — DA line_items → TimelineEvent
- `backend/app/services/sentinel/noon_report_normalizer.py` — EmissionReport → TimelineEvent
- `backend/app/services/sentinel/audit_engine.py` — S-001, S-002, S-003 rules
- `backend/tests/test_audit_engine.py` — Existing unit tests
