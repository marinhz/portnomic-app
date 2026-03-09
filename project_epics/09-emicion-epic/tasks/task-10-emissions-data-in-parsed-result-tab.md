# Task 9.10 — Add emissions data to Parsed Result tab

**Epic:** [09-emicion-epic](../epic.md)

**Type:** Feature

---

## Objective

Enhance the Parsed Result tab in Email Detail so that when viewing a parsed Noon/Bunker report (emission email), users see the extracted fuel data and calculated emissions (CO₂, EUA estimate) directly in the email view, without having to navigate to the emission report.

---

## Problem statement

- User opens an email that was parsed as a Noon/Bunker report.
- The Parsed Result tab currently shows vessel/port metadata (often "—" for emission reports) and a "View emission report" link.
- **Missing:** Fuel entries table, CO₂ total, EUA estimate, report date, distance — the key data operators need at a glance.
- Users must click through to the emission report to see this information.

---

## Scope

### Data to display in Parsed Result tab (for emission emails)

1. **Extraction data** (from `email.ai_raw_output`):
   - Report date
   - Distance (nm)
   - Fuel entries table: fuel type, consumption (MT), operational status

2. **Calculated emissions** (from emission report or parse job result):
   - Total CO₂ (MT)
   - EUA estimate (€)
   - Compliance status (Green/Yellow/Red badge)

### Implementation options

- **Option A:** When `parseJob.result` has `emission_report_id`, fetch `GET /api/v1/emissions/reports/{id}` to get full report (co2_mt, eua_estimate_eur, fuel_breakdown, compliance_status). Use this for both fresh parse and when user returns to the page — requires fetching parse job by email_id on load when email is completed.
- **Option B:** Add `emission_report_id` to `EmailResponse` when the email is linked to an emission report (backend: lookup EmissionReport by email_id). Frontend fetches emission report when present.
- **Option C:** Include calculated emissions in parse job result (already present: `emissions`, `eua_estimate` in job.result for emission parses). Use parse job result when available; otherwise fetch emission report by ID if we can obtain it (e.g. from a new email field or dedicated endpoint).

### UI layout

- Reuse existing Parsed Result card structure.
- For emission emails: show vessel, report date, distance; fuel entries table (similar to line items table); emissions summary (CO₂, EUA, compliance badge); "View emission report" link.
- Handle both states: (1) emission report exists — show full data; (2) only raw extraction in ai_raw_output — show fuel_entries and extraction fields, optionally "View report" if report exists.

### Backend considerations

- If Option B: Add `emission_report_id: uuid | null` to `EmailResponse` when `EmissionReport.email_id = email.id` exists.
- Optional: `GET /api/v1/emissions/reports/by-email/{email_id}` — returns emission report for a given source email (convenience endpoint).

---

## Acceptance criteria

- [ ] Parsed Result tab shows fuel entries table when `ai_raw_output` contains `fuel_entries`.
- [ ] Parsed Result tab shows report date and distance when present in extraction.
- [ ] Parsed Result tab shows CO₂ (MT) and EUA estimate (€) when emission report data is available.
- [ ] Compliance status badge (Green/Yellow/Red) displayed when available.
- [ ] "View emission report" link remains; layout consistent with existing DA/port-call parsed result styling.
- [ ] No crash when `line_items` is missing (emission emails) — already handled per Task 2.13.

---

## Related code

- `frontend/src/pages/emails/EmailDetail.tsx` — Parsed Result section, `parsedResult`, `lineItems`, `emissionReportId`
- `frontend/src/api/types.ts` — `ParsedEmailResult`, `EmissionReportDetailResponse`, `EmissionFuelBreakdown`
- `backend/app/schemas/email.py` — `EmailResponse` (add `emission_report_id` if Option B)
- `backend/app/routers/emissions.py` — `GET /reports/{id}`
- `backend/app/services/parse_worker.py` — job.result structure for emission parses (`emissions`, `eua_estimate`, `extraction`)

---

## Dependencies

- Task 9.1 (extraction schema, fuel_entries).
- Task 9.3 (calculation engine — CO₂, EUA).
- Task 9.7 (Emissions Dashboard, report detail).
- Task 2.13 (parse success, safe handling of emission vs DA parsed result).
