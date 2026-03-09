# Task 9.3 — Calculation Engine (C-Engine)

**Epic:** [09-emicion-epic](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Implement the calculation engine that converts extracted fuel consumption data into CO₂ emissions and EU ETS financial impact. Uses the formula \( E = C \times f \) and emission factors from Task 9.1.

---

## Scope

### CO₂ calculation

- For each fuel entry: `E = consumption_mt × emission_factor`.
- Aggregate total CO₂ per report (and per voyage if multiple reports).
- Emission factors from config (Task 9.1).

### EU ETS integration (estimation)

- **EUA calculation:** Determine number of EU Allowances required for the voyage segment (EU port calls, EU waters).
- **Formula:** EUAs ≈ CO₂ (t) × applicable factor (e.g. 100% for EU port, 50% for EU waters — simplify for MVP).
- Reference: EU ETS Maritime rules (phase-in 2024–2026).

### Service interface

- `calculate_emissions(report: EmissionReport) -> EmissionsResult` — returns total_co2_mt, per_fuel_breakdown.
- `estimate_eua(report: EmissionReport, carbon_price_eur: float) -> EUAEstimate` — returns eua_count, cost_eur.

---

## Acceptance criteria

- [ ] C-Engine calculates CO₂ from consumption and emission factors.
- [ ] EUA estimation returns count and cost (given carbon price).
- [ ] Results are deterministic and auditable (formula + factors documented).

---

## Related code

- `backend/app/services/emission_calculator.py` — C-Engine
- `backend/app/schemas/emission.py` — EmissionsResult, EUAEstimate

---

## Dependencies

- Task 9.1 (data model, emission factors).
- Task 9.4 (carbon price) — or pass price as parameter for MVP.
