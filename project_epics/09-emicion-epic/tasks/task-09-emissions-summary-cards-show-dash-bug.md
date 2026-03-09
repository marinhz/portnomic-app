# Task 9.9 — Bug: Emissions Dashboard summary cards show "—" despite API returning valid data

**Epic:** [09-emicion-epic](../epic.md)

**Type:** Bug

---

## Objective

Fix the bug where the Emissions Dashboard summary cards (Total CO₂, EUA Est., Voyages, Compliance) display "—" even when the API returns valid data.

---

## Problem statement

- User navigates to the Emissions Dashboard (`/emissions`).
- API `GET /api/v1/emissions/summary` returns valid data, e.g.:
  ```json
  {
    "data": {
      "compliance": { "green": 2, "yellow": 0, "red": 0 },
      "total_co2_mt": 270.52,
      "total_eua_estimate_eur": 11488.85,
      "voyage_count": 2
    }
  }
  ```
- **Expected:** Summary cards display the values (270.52, €11,488.85, 2, green/yellow/red counts).
- **Actual:** All four cards show "—" instead of the API values.

---

## Scope

- **Root cause analysis:** Identify why the frontend does not render the summary data even when the API response is correct.
- **Possible causes:**
  - Response shape mismatch: backend returns `SingleResponse` with payload wrapped in `{ data: T }`; frontend may be reading `res.data` instead of `res.data.data`.
  - Type coercion or falsy checks (e.g. `summary?.total_co2_mt` treating valid `0` as empty).
  - State not being updated with the correct payload.
- **Fix:** Ensure the summary state is set from the correct property of the API response.
- **Verification:** Summary cards display values when API returns non-empty data.

---

## Root cause (to be documented)

The backend `GET /api/v1/emissions/summary` returns a `SingleResponse`:

```json
{ "data": { "total_co2_mt": 270.52, "total_eua_estimate_eur": 11488.85, "voyage_count": 2, "compliance": { "green": 2, "yellow": 0, "red": 0 } } }
```

In `EmissionsDashboard.tsx`, the summary fetch uses:

```ts
setSummary(res.data);
```

Axios `res.data` is the full response body `{ data: { ... } }`, not the inner summary object. The actual summary is in `res.data.data`. Other endpoints (e.g. `EmailDetail`, `EmissionsReportDetail`, `DADetail`) correctly use `res.data.data` for single-item responses.

**Fix:** Change `setSummary(res.data)` to `setSummary(res.data.data)`.

---

## Acceptance criteria

- [ ] Root cause documented.
- [ ] Summary cards display Total CO₂ (MT), EUA Est. (€), Voyages, and Compliance when API returns valid data.
- [ ] No "—" shown when API returns non-empty summary.
- [ ] Consistent with other single-response API usage in the codebase (e.g. `res.data.data`).

---

## Related code

- `frontend/src/pages/emissions/EmissionsDashboard.tsx` — summary fetch, `setSummary(res.data)` (line ~172)
- `backend/app/routers/emissions.py` — `get_emissions_summary` returns `SingleResponse[EmissionsSummaryResponse]`
- `backend/app/schemas/common.py` — `SingleResponse` wraps payload in `data`
- Reference: `EmailDetail.tsx`, `EmissionsReportDetail.tsx`, `DADetail.tsx` — use `res.data.data` for single responses

---

## Dependencies

- Task 9.7 (Emissions Dashboard UI).
- Task 9.8 (Emissions Dashboard values not updating) — different bug (stale data vs. wrong response parsing).
