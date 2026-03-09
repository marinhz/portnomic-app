# Task 2.13 — Bug: Parse email success redirects to 404 page

**Epic:** [02-ai-processing](../epic.md)

**Type:** Bug

---

## Objective

Fix the bug where users are incorrectly redirected to a 404 page with an error when email parsing completes successfully.

## Problem statement

- User triggers AI parse for an email (e.g. "Parse with AI" button).
- Parse completes successfully on the backend.
- Instead of showing the parsed result or redirecting to the correct view, the user is redirected to a 404 page with an error.
- Expected: User sees parsed data, report detail, or email detail with parsed result.
- Actual: User sees 404 page.

## Scope

- **Root cause analysis:** Identify why successful parse triggers a redirect to a non-existent route.
- **Possible causes:**
  - Frontend redirect/navigation uses wrong URL after parse completion (e.g. invalid route, wrong ID).
  - Route does not exist for the destination (e.g. `/reports/{id}` or `/emails/{id}/parsed`).
  - API response returns redirect URL or resource ID that does not match any frontend route.
  - Polling/subscription callback navigates before route is ready or with stale/invalid params.
- **Fix:** Correct the post-parse navigation flow so successful parse leads to the appropriate view (email detail with parsed data, report view, or parse result panel).
- **Logging:** Add or verify logs to trace redirect/navigation path for debugging.

## Root cause (documented)

- **No explicit redirect on parse success** — EmailDetail stays on page and refetches email.
- **Possible causes of 404**: (1) Wrong path if "View report" used `/reports/{id}` instead of `/emissions/reports/{id}`; (2) Unsafe access to `parsedResult.line_items` when emission emails have `fuel_entries` instead, causing crash; (3) Race when refetching email after parse.
- **Fix applied**: Safe parsing with optional chaining, "View emission report" link uses correct path `/emissions/reports/{id}`, error handling for refetch, debug logging.

## Acceptance criteria

- [x] Root cause documented.
- [x] When parse completes successfully, user is shown the parsed result (or correct detail view) — no 404.
- [x] Error states (parse failed) still show appropriate error UI, not 404.
- [x] Navigation/redirect logic is consistent across parse trigger entry points (email list, email detail, etc.).

## Related code

- `frontend/src/pages/emails/` — EmailDetail, parse trigger UI, post-parse navigation
- `frontend/src/routes/` — Route definitions (ensure destination routes exist)
- `frontend/src/` — Parse status polling, success/error handlers
- [Task 2.12](task-12-frontend-parse-trigger-status.md) — Frontend parse trigger and status

---

## Dependencies

- Task 2.12 (Frontend parse trigger and status).
