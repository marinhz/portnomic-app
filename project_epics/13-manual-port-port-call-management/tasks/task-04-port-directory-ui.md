# Task 13.4 — Port Directory UI

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev**, **react-router-v7**, and **tailwind-design-system** skills.

---

## Objective

Build the Port Directory page at `/directory/ports` with searchable list, "Add Port" modal, and link to Tariff Configuration per port.

---

## Scope

- **Route:** `/directory/ports` (add to router under app layout).
- **List:** DataTable with search input; columns: Name, Country, UN/LOCODE, Timezone, Actions.
- **Add Port modal:** Fields: Name, Country, UN/LOCODE, Coordinates (lat/lon), Timezone.
- **Per-row action:** Link to Tariff Configuration (e.g. `/tariffs?port_id={id}` or existing tariff route).
- Sidebar/nav: Add "Directory" or "Ports" entry if not present.

---

## Acceptance criteria

- [ ] Port Directory page loads at `/directory/ports`.
- [ ] Search filters the list client- or server-side.
- [ ] Add Port modal creates port via API.
- [ ] Each port links to Tariff Configuration.
