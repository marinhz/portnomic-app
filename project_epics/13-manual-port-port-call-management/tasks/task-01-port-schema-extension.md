# Task 13.1 — Port Schema Extension (Coordinates, UN/LOCODE)

**Epic:** [13-manual-port-port-call-management](../epic.md)

---

## Agent

Use the **Backend** agent with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Extend the Port model to support Coordinates and ensure UN/LOCODE is clearly represented (current `code` field maps to UN/LOCODE). Add latitude/longitude for geographic data.

---

## Scope

- Add `latitude` and `longitude` columns (nullable) to `ports` table, or a single `coordinates` JSONB column.
- Document that `code` is UN/LOCODE (e.g. NLRTM, SGSIN).
- Update `PortCreate`, `PortUpdate`, `PortResponse` schemas.
- Alembic migration.

---

## Acceptance criteria

- [ ] Port model supports coordinates (lat/lon or JSONB).
- [ ] Schemas include coordinates in create/update/response.
- [ ] Migration runs cleanly.
