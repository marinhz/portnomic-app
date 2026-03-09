# Task 9.7 — Emissions Dashboard UI

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

Build the Emissions Dashboard UI: visual representation of carbon debt per voyage, compliance status (Green/Yellow/Red vs FuelEU Maritime intensity targets), and activity logs with links to original emails for audit transparency.

---

## Scope

### Routes

- **/emissions** or **/reports/emissions** — Main dashboard (protected, tenant-scoped).
- **/emissions/reports/{id}** — Report detail with export actions.

### Dashboard components

- **Carbon debt per voyage:** Summary cards or chart showing CO₂ (MT) and estimated EUA cost per voyage.
- **Compliance status:** Green / Yellow / Red indicator — simple rules for MVP (e.g. Green: within target; Yellow: approaching; Red: over).
- **Activity logs:** Table/list of emission reports — date, vessel, CO₂, status (verified/flagged), link to source email.
- **Filters:** By vessel, date range, status.

### Report detail

- Full emission data, fuel breakdown, CO₂, EUA estimate.
- Anomaly flags (if any) with explanation.
- Actions: Export (JSON/XML/PDF), link to source email.

### API integration

- **GET /api/v1/emissions/reports** — List reports (paginated, filterable).
- **GET /api/v1/emissions/reports/{id}** — Report detail.
- **GET /api/v1/emissions/summary** — Aggregated carbon debt, compliance (optional).

---

## Acceptance criteria

- [ ] Dashboard shows carbon debt and compliance status.
- [ ] Activity logs list reports with link to source email.
- [ ] Report detail shows full data and export actions.
- [ ] UI follows ShipFlow design system (shadcn, Tailwind).

---

## Related code

- `frontend/src/pages/emissions/` — dashboard, report detail
- `frontend/src/routes/` — route definitions
- API client for emissions endpoints

---

## Dependencies

- Task 9.1–9.6 (backend APIs).
- Epic 7 (shadcn, design system) — or existing UI patterns.
