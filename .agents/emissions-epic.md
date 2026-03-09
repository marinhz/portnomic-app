# Emissions Epic Agent — Eco-Compliance & Emissions Reporting (Epic 9)

**Use for:** All tasks in `project_epics/09-emicion-epic/` — AI-driven fuel & emission analytics, EU ETS, FuelEU Maritime compliance.

**Compliance target:** EU ETS (Emission Trading System) & FuelEU Maritime (2026 standards)

---

## Task → Agent Mapping

| Task | Agent | Skills | Task File |
|------|-------|--------|-----------|
| 9.1 Emission data model & extraction schema | **Backend** | fastapi-python, python-project-structure | [task-01](project_epics/09-emicion-epic/tasks/task-01-emission-data-model-extraction-schema.md) |
| 9.2 Noon / bunker report AI parser | **Backend** | fastapi-python, python-project-structure | [task-02](project_epics/09-emicion-epic/tasks/task-02-noon-bunker-report-ai-parser.md) |
| 9.3 Calculation engine (C-Engine) | **Backend** | fastapi-python | [task-03](project_epics/09-emicion-epic/tasks/task-03-calculation-engine.md) |
| 9.4 Carbon price API integration | **Backend** | fastapi-python | [task-04](project_epics/09-emicion-epic/tasks/task-04-carbon-price-api-integration.md) |
| 9.5 Anomaly detection (AI Auditor) | **Backend** | fastapi-python | [task-05](project_epics/09-emicion-epic/tasks/task-05-anomaly-detection.md) |
| 9.6 EU MRV verification export | **Backend** | fastapi-python | [task-06](project_epics/09-emicion-epic/tasks/task-06-eu-mrv-verification-export.md) |
| 9.7 Emissions dashboard UI | **Frontend** | react-dev, react-router-v7, tailwind-design-system | [task-07](project_epics/09-emicion-epic/tasks/task-07-emissions-dashboard-ui.md) |

**Backend tasks (9.1–9.6):** See [backend.md](backend.md).  
**Frontend task (9.7):** See [frontend.md](frontend.md).

---

## Domain Context

### AI Data Extraction (NLP Layer)

- **Input sources:** Plain text emails, PDF attachments, Excel Noon Reports.
- **Trigger:** Email Parser detects "Noon Report" or "Bunker Report" → route to emission parser.
- **Target data:** Vessel (name, IMO), fuel type (VLSFO, LSMGO, MGO, LNG, biofuels), consumption (MT), operational_status (at_sea_cruising | at_berth | at_anchor), distance_nm.

### Extraction JSON Schema (LLM output)

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

### C-Engine (Calculation Engine)

- **CO₂ formula:** \( E = C \times f \) — E = emissions (MT), C = consumption (MT), f = emission factor (e.g. VLSFO ≈ 3.114 tCO₂/t fuel).
- **EU ETS:** EUAs ≈ CO₂ (t) × applicable factor; cost = EUAs × carbon_price_eur.
- **Emission factors:** IMO / EU MRV defaults; config in `config.py` or `constants.py`.

### Anomaly Detection (AI Auditor)

- **Rule 1:** Consumption vs distance — flag if consumption/distance ratio outside plausible band (e.g. 0.01–0.1 MT/NM for large vessels).
- **Rule 2:** Fuel type vs vessel profile — if vessel has `fuel_types`, flag unknown/mismatched fuel.
- **Output:** `anomaly_flags: [{ rule, description, severity }]`; status `verified | flagged | failed`.

### EU MRV Export

- **Formats:** JSON, XML, PDF.
- **Data:** Vessel (IMO, name), period, fuel by type, CO₂, distance, time in port (EU).
- **Reference:** EU MRV Regulation (EU) 2015/757; include source email link for audit.

### API Endpoints (to implement)

- `POST /api/v1/emissions/parse` — Submit email for emission parse; returns job id.
- `GET /api/v1/emissions/parse/{job_id}` — Status and result.
- `GET /api/v1/emissions/reports` — List reports (paginated, filterable).
- `GET /api/v1/emissions/reports/{id}` — Report detail.
- `GET /api/v1/emissions/reports/{id}/export?format=json|xml|pdf` — MRV export.
- `GET /api/v1/emissions/summary` — Aggregated carbon debt, compliance (optional).

---

## Related Code (Backend)

| Component | Path |
|-----------|------|
| EmissionReport model | `backend/app/models/emission_report.py` |
| Emission schemas | `backend/app/schemas/emission.py` |
| Emission factors | `backend/app/config.py` or `constants.py` |
| Emission parser service | `backend/app/services/emission_parser.py` |
| Emission parse worker | `backend/app/workers/emission_parse_worker.py` or extend `parse_worker.py` |
| C-Engine | `backend/app/services/emission_calculator.py` |
| Carbon price service | `backend/app/services/carbon_price.py` |
| Anomaly detection | `backend/app/services/emission_anomaly.py` |
| MRV export | `backend/app/services/emission_export.py` |
| Emissions router | `backend/app/routers/emissions.py` |

---

## Related Code (Frontend)

| Component | Path |
|-----------|------|
| Dashboard | `frontend/src/pages/emissions/` |
| Report detail | `frontend/src/pages/emissions/reports/[id]` |
| Routes | `frontend/src/routes/` |
| API client | Emissions endpoints |

---

## Dependencies

- **Epic 2 (AI processing):** LLM client, parse job queue, prompt/schema pattern.
- **Epic 6 (Email):** Email ingest; trigger on Noon Report / Bunker Report detection.
- **Vessel entity:** IMO; optional technical profile (fuel_types) for anomaly Rule 2.
- **Existing:** `parse_worker.py`, `llm_client.py`, `parse_job_service.py`, `prompts.py`.

---

## Conventions

- All emission data tenant-scoped; `tenant_id` on EmissionReport.
- Link EmissionReport to source Email for audit trail.
- Use existing patterns: Pydantic schemas, async services, HTTPException, dependency injection.
- Carbon price: cache (Redis/in-memory) with TTL; fallback to env var on API failure.
