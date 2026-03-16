# Task 13.8 — Tariff Management UI

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev** and **tailwind-design-system** skills.

---

## Objective

Replace the placeholder "No tariffs configured for this port yet" message on the Tariff Configuration page with full tariff management UI: create, edit, and view tariffs per port.

---

## Scope

- **Location:** `/directory/tariff-config?port_id=...` (existing TariffConfig page).
- **Empty state:** Replace placeholder with "Add Tariff" CTA instead of "Tariff management UI can be added in a future task."
- **Create tariff:** Modal or form to add a new tariff:
  - `name` (required)
  - `valid_from` (required, date)
  - `valid_to` (optional, date)
  - `formula_config` — structured form for line items:
    - Each item: `description`, `type` (per_call | per_ton | per_hour | fixed), `rate`, `currency`
    - `tax_rate` (number)
    - Default currency (e.g. USD)
- **Edit tariff:** Same form, pre-filled; call `PUT /api/v1/tariffs/{id}`.
- **View:** Existing read-only table stays; add Edit action per row.
- **API:** Backend already provides `POST /tariffs`, `PUT /tariffs/{id}`, `GET /tariffs` (list by port_id).

---

## Formula config structure (reference)

```json
{
  "items": [
    {
      "description": "Pilotage",
      "type": "per_call",
      "rate": 150.0,
      "currency": "USD"
    }
  ],
  "tax_rate": 0.0,
  "currency": "USD"
}
```

Types: `per_call`, `per_ton`, `per_hour`, `fixed`.

---

## Acceptance criteria

- [ ] Empty state shows "Add Tariff" CTA instead of placeholder text.
- [ ] User can create a new tariff with name, valid_from, valid_to, and formula_config (line items + tax_rate).
- [ ] User can edit an existing tariff via row action.
- [ ] Create/update calls existing API; list refreshes after success.
- [ ] Styling matches existing Port Directory / TariffConfig design system.

---

## Out of scope (for this task)

- Delete tariff (no backend endpoint; can be added in a follow-up).
- Tariff versioning UI (version is auto-incremented by backend).
- Import/export of tariff configs.
