# Task 12.8 — DA List: Leakage Detector Filter & Icon

**Epic:** [12-ai-leakage-detector](../epic.md)

---

## Agent

Use the **Frontend** agent with **react-dev** and **tailwind-design-system** skills. Backend changes require **fastapi-python** skill.

---

## Objective

Improve discoverability of DAs with Leakage Detector findings in the Disbursement Accounts list. Implement either (or both):

1. **Filter:** Allow users with the Leakage Detector premium feature to filter the DA list to show only DAs that have anomalies.
2. **Icon:** Show an icon in the DA grid indicating which DAs have Leakage Detector findings — visible only to users who have both the premium feature and `da:read` permission.

---

## Scope

### Option A — Filter (premium users only)

- **Location:** `/da` (DAList page), alongside existing status filter.
- **Filter control:** Add "Has Leakage" or "With Anomalies" filter button/chip.
- **Visibility:** Filter control visible only when `user.leakage_detector_enabled === true` (or `isPlatformAdmin`).
- **API:** Backend `GET /da` supports query param `has_anomalies=true`; returns only DAs that have at least one anomaly.
- **Empty state:** When filter active and no results: "No DAs with Leakage Detector findings."

### Option B — Icon in grid (permission-gated)

- **Location:** `/da` (DAList table), add a column or icon in each row.
- **Icon:** Badge or icon (e.g. shield-check, alert-triangle) indicating the DA has anomalies.
- **Visibility:** Icon column/indicator visible only when user has `leakage_detector_enabled` and `da:read`.
- **API:** Backend `GET /da` list response includes `has_anomalies: boolean` per DA (or equivalent field).
- **Tooltip:** Hover on icon shows "Has Leakage Detector findings" or similar.

### Backend requirements

- **DA list endpoint:** Extend `GET /api/v1/da`:
  - Query param: `has_anomalies=true` — filter to DAs with at least one Anomaly record.
  - Response: Add `has_anomalies: boolean` to each DA in list (subquery or join on Anomaly.da_id).
- **Feature gate:** `has_anomalies` filter and `has_anomalies` field in response should only be applied/returned when tenant has Leakage Detector (Professional/Enterprise). For Starter plans, omit the field and ignore the filter (or return 403 if filter used).

---

## Acceptance criteria

- [ ] **Filter (Option A):** Users with Leakage Detector premium see "Has Leakage" filter; selecting it shows only DAs with anomalies.
- [ ] **Icon (Option B):** Users with Leakage Detector premium and `da:read` see an icon in the DA grid for DAs that have anomalies.
- [ ] Filter and icon are hidden for Starter plans (no premium feature).
- [ ] Backend returns `has_anomalies` and supports `has_anomalies` filter; feature-gated appropriately.
- [ ] Styling matches existing DA list and design system.

---

## Out of scope (for this task)

- Anomaly count in list (e.g. "3 anomalies") — can be a follow-up.
- Sorting by anomaly count or severity.
- Leakage Detector page changes (handled in Task 12.5).

---

## Related code

- `frontend/src/pages/da/DAList.tsx` — DA list page, status filter, table
- `frontend/src/api/types.ts` — `DAListResponse` (add `has_anomalies?: boolean`)
- `backend/app/routers/da.py` — DA list endpoint
- `backend/app/models/anomaly.py` — Anomaly model (da_id FK)

---

## Dependencies

- Task 12.1 — Anomaly table
- Task 12.7 — Sidebar icon & feature gating (leakage_detector_enabled in user context)
- Epic 8 — Plan tiers, limits service
