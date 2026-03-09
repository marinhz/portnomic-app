# Task 9.1 — Emission Data Model & Extraction Schema

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Define the data model for emission reports and the JSON extraction schema that the LLM will populate when parsing Noon Reports and Bunker Reports. This schema is the contract between the AI parser and the calculation engine.

---

## Scope

### Data model

- **EmissionReport** (or equivalent) entity: tenant-scoped; linked to vessel (IMO), port call (optional), email (source); report date; fuel entries (fuel_type, consumption_mt, operational_status); distance_nm; extracted_at; schema_version.
- **FuelEntry** (embedded or separate): fuel_type (enum: VLSFO, LSMGO, MGO, LNG, biofuels, etc.), consumption_mt, operational_status (at_sea_cruising | at_berth | at_anchor).
- Migrations: new table(s); indexes for tenant_id, vessel_id, report_date.

### Extraction JSON schema (LLM output)

```json
{
  "vessel_name": "string",
  "imo_number": "string",
  "report_date": "YYYY-MM-DD",
  "fuel_entries": [
    {
      "fuel_type": "VLSFO|LSMGO|MGO|LNG|biofuels|...",
      "consumption_mt": 12.5,
      "operational_status": "at_sea_cruising|at_berth|at_anchor"
    }
  ],
  "distance_nm": 245.0
}
```

### Emission factors config

- Config or constants: emission factor per fuel type (e.g. VLSFO ≈ 3.114 tCO₂/t fuel).
- Reference: IMO / EU MRV default factors.

---

## Acceptance criteria

- [x] EmissionReport (or equivalent) model exists with migrations.
- [x] JSON extraction schema is versioned and documented.
- [x] Emission factors config exists for common fuel types (VLSFO, MGO, LNG, etc.).

---

## Related code

- `backend/app/models/emission_report.py` — new model
- `backend/app/schemas/emission.py` — Pydantic schemas
- `backend/app/config.py` or `constants.py` — emission factors

---

## Dependencies

- Vessel entity with IMO (Epic 1 or existing).
- Email entity (Epic 2).
