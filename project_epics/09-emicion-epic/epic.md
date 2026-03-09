# Epic 9 — Eco-Compliance & Emissions Reporting

**Source:** Technical Specification (main-file.md) — AI-Driven Fuel & Emission Analytics  
**Compliance target:** EU ETS (Emission Trading System) & FuelEU Maritime (2026 standards)  
**Duration (estimate):** 4–5 weeks

---

## Agent assignments

| Task | Agent | Skills |
|------|-------|--------|
| 9.1 Emission data model & extraction schema | Backend | fastapi-python, python-project-structure |
| 9.2 Noon / bunker report AI parser | Backend | fastapi-python, python-project-structure |
| 9.3 Calculation engine (C-Engine) | Backend | fastapi-python |
| 9.4 Carbon price API integration | Backend | fastapi-python |
| 9.5 Anomaly detection (AI Auditor) | Backend | fastapi-python |
| 9.6 EU MRV verification export | Backend | fastapi-python |
| 9.7 Emissions dashboard UI | Frontend | react-dev, react-router-v7, tailwind-design-system |

---

## Objective

Automate the extraction of fuel consumption data from non-structured sources (Captain's Noon Reports, Arrival/Departure emails, bunker reports) and convert it into verified carbon emission reports. This solves the regulatory burden for ship owners and agents by ensuring data accuracy and minimizing the risk of EU financial penalties.

---

## Scope

### AI data extraction (NLP layer)

- **Input sources:** Plain text emails, PDF attachments, Excel Noon Reports.
- **Trigger:** Automated via the Email Parser module once a "Noon Report" or "Bunker Report" is detected.
- **Target data points:** Vessel (name, IMO), fuel type (VLSFO, LSMGO, MGO, LNG, biofuels), consumption (MT), operational status (at sea / at berth / at anchor), distance travelled.

### Calculation engine (C-Engine)

- **CO₂ formula:** \( E = C \times f \) — E = emissions (MT), C = consumption (MT), f = emission factor (e.g. ~3.114 for VLSFO).
- **EU ETS:** Calculate EU Allowances (EUAs) required for the voyage; cost projection via current carbon market price.

### Key features

- **Anomaly detection (AI Auditor):** Flag reports where consumption is physically impossible for distance covered, or fuel types do not match vessel technical profile.
- **One-click verification export:** EU MRV (Monitoring, Reporting, Verification) compliant report — JSON/XML for submission, PDF for verifiers (DNV, Lloyd's Register).

### UI/UX

- **Emissions dashboard:** Carbon debt per voyage, compliance status (Green/Yellow/Red vs FuelEU Maritime intensity targets).
- **Activity logs:** History of extracted data with links to original email for audit.

---

## Out of scope (for this epic)

- Full FuelEU Maritime intensity calculation formulas (can be added later).
- Direct submission to EU authorities (export only; manual submission).
- Vessel technical profile CRUD (assume profile exists or is imported).

---

## Acceptance criteria

- [ ] Noon/bunker reports are parsed by LLM and structured emission data is persisted.
- [ ] C-Engine calculates CO₂ emissions and EU ETS cost projection.
- [ ] Anomaly detection flags impossible consumption and fuel-type mismatches.
- [ ] EU MRV compliant export (JSON/XML/PDF) is available.
- [ ] Emissions dashboard shows carbon debt, compliance status, and activity logs with email links.

---

## Dependencies

- Epic 2 (AI processing) — LLM client, parse job queue, prompt/schema pattern.
- Epic 6 (Email connection) — Email ingest; trigger on Noon Report / Bunker Report detection.
- Vessel entity with IMO and optional technical profile (fuel types, capacity).

---

## Business value

| Feature | Customer pain | Solution |
|---------|---------------|----------|
| Auto-extraction | Manual entry takes 2 hours/day | Done in seconds by AI |
| Error checking | Human typos lead to €100k+ fines | AI flags discrepancies instantly |
| ETS projection | Unknown carbon costs | Real-time financial forecasting |
