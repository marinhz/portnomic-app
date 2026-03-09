# Task 3.1 — Tariff entity and API

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Store and version port-specific tariff configurations; expose CRUD or list/create/update API (EDD §5.1, §9.1).

## Scope

- **Tariff:** tenant_id, port_id, name, version, formula_config (JSON), valid_from, valid_to.
- Formula config: formula or table-driven (e.g. per-call fees, per-ton fees) (EDD §9.1).
- API: list tariffs (by port/tenant), create, update; get active tariff for port at a given date (versioning).
- Permissions: e.g. da:read / da:write or tariff:read / tariff:write.

## Acceptance criteria

- [ ] Tariffs are stored with version and validity period; multiple versions per port supported.
- [ ] API allows creating and updating tariffs; listing filtered by tenant and optionally port.
- [ ] Formula engine can resolve active tariff for a port and date (Task 3.3).
