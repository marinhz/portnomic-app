# Task 9.6 — EU MRV Verification Export

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Generate EU MRV (Monitoring, Reporting, Verification) compliant reports for direct submission or for independent verifiers (e.g. DNV, Lloyd's Register). Support JSON, XML, and PDF formats.

---

## Scope

### EU MRV compliance

- **Data required:** Vessel (IMO, name), reporting period, fuel consumption by type, CO₂ emissions, distance, time in port (EU), etc.
- **Format:** Align with EU MRV Regulation (EU) 2015/757 and delegated acts.
- **Reference:** EU MRV templates/schemas (check official EU documentation for exact structure).

### Export formats

- **JSON:** Structured data for API submission or system integration.
- **XML:** Alternative format for some verifiers/systems.
- **PDF:** Human-readable report for verifiers; include all key data, vessel info, emission summary, audit trail reference.

### API

- **GET /api/v1/emissions/reports/{id}/export?format=json|xml|pdf** — Generate and return file.
- **Query params:** `format` (required), optional `voyage_id` for voyage-level aggregation.

### Implementation

- Template or schema for each format.
- PDF: Use reportlab, weasyprint, or similar; or generate HTML and convert.
- Include link to source email(s) in export for audit transparency.

---

## Acceptance criteria

- [ ] Export endpoint returns JSON, XML, or PDF.
- [ ] Export contains all MRV-required data (vessel, period, fuel, CO₂, distance).
- [ ] PDF is readable and suitable for verifier submission.
- [ ] Source email reference included for audit trail.

---

## Related code

- `backend/app/services/emission_export.py` — export logic
- `backend/app/routers/emissions.py` — export endpoint
- `backend/app/templates/emission_*.html` or equivalent for PDF

---

## Dependencies

- Task 9.1, 9.2, 9.3 (data model, parsed data, calculations).
