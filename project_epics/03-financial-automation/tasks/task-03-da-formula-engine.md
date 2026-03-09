# Task 3.3 — DA formula engine

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Compute DA line items and totals from port call, vessel, port, tariff (versioned), and optional AI-parsed line items (EDD §9.1).

## Scope

- **Inputs:** PortCall, Vessel, Port, Tariff (active for port/date), optional parsed line items from Email.
- **Output:** Line items (description, quantity, unit price, amount, currency); subtotals and totals.
- Tariff formula_config drives calculation (table or formula); version stored with DA for audit (EDD §9.1).
- Idempotent for same inputs; deterministic output.

## Acceptance criteria

- [ ] Engine produces correct line items and totals for given port call and tariff.
- [ ] AI-parsed line items can be merged or used as base; tariff rules applied consistently.
- [ ] DA version and tariff version stored for audit trail.
