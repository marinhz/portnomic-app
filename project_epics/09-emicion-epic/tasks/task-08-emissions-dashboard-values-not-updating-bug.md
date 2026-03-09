# Task 9.8 — Bug: Emissions Dashboard values do not update after processing emission emails

**Epic:** [09-emicion-epic](../epic.md)

**Type:** Bug

---

## Objective

Fix the bug where the Emissions Dashboard values (carbon debt, compliance status, activity logs) do not change after the user processes 2 or more emission emails. The dashboard continues to show stale or empty data instead of reflecting newly parsed reports.

---

## Problem statement

- User processes emission emails (e.g. noon reports, bunker reports) via AI parse.
- Parse completes successfully and emission reports are created on the backend.
- User navigates to the Emissions Dashboard.
- **Expected:** Dashboard shows updated values — carbon debt, compliance status, and activity logs include the newly processed reports.
- **Actual:** Dashboard values do not change; user still sees old or empty data even after 2+ emission emails have been processed.

---

## Scope

- **Root cause analysis:** Identify why the dashboard does not reflect newly created emission reports.
- **Possible causes:**
  - Dashboard data is fetched once on mount and never refetched (no invalidation after parse).
  - Caching layer (React Query, SWR, etc.) serves stale data; cache keys or invalidation missing.
  - No real-time or polling mechanism to detect new reports.
  - Backend summary/aggregation endpoints not including newly created reports (e.g. wrong filters, timing).
  - Frontend does not invalidate emissions queries when parse completes or when navigating to dashboard.
  - Race condition: dashboard loads before backend has finished persisting/aggregating new reports.
- **Fix:** Ensure dashboard data is refreshed when:
  - User navigates to the dashboard (e.g. after parse).
  - New emission reports are created (invalidate on parse success).
  - User manually refreshes or after a reasonable interval (polling, if applicable).
- **Logging:** Add or verify logs to trace data flow and refresh timing.

---

## Root cause (documented)

1. **No invalidation after parse:** When emission emails were parsed successfully in EmailDetail, the EmissionsDashboard had no way to know new reports existed. It only fetched on mount and when filter params changed.
2. **No refetch on navigation focus:** When the user navigated back to the dashboard (e.g. from "View emission report" or sidebar), the component remounted and refetched — but if the dashboard stayed mounted (e.g. in another tab) while the user parsed in the current tab, it never refetched.
3. **No visibility-based refresh:** When the user switched tabs and returned, the dashboard did not refetch.

**Fix applied:**
- Added `emission-report-created` custom event dispatched by EmailDetail when parse completes with `emission_report_id`.
- EmissionsDashboard listens for this event and refetches summary + reports.
- Added `location.key` to effect deps so data refetches on every navigation to the dashboard.
- Added `visibilitychange` listener to refetch when the user returns to the tab.

---

## Acceptance criteria

- [x] Root cause documented.
- [x] After processing 2+ emission emails, dashboard shows updated carbon debt and compliance values.
- [x] Activity logs list the newly processed reports with links to source emails.
- [x] Dashboard refetches or invalidates when user returns from parse flow (e.g. "View emission report" or navigating back to dashboard).
- [x] No stale data after successful parse; cache invalidation is correct.

---

## Related code

- `frontend/src/pages/emissions/` — Dashboard components, data fetching
- `frontend/src/` — Query invalidation on parse success, navigation after parse
- API client for emissions endpoints (`/api/v1/emissions/reports`, `/api/v1/emissions/summary`)
- [Task 9.7](task-07-emissions-dashboard-ui.md) — Emissions Dashboard UI
- [Task 2.12](../../02-ai-processing/tasks/task-12-frontend-parse-trigger-status.md) — Frontend parse trigger and status (post-parse flow)

---

## Dependencies

- Task 9.7 (Emissions Dashboard UI).
- Task 2.12 (Frontend parse trigger and status) — for post-parse invalidation flow.
