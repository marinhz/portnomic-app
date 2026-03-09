# Task 2.12 — Frontend: trigger parse and show job status/result

**Epic:** [02-ai-processing](../epic.md)

---

## Objective

Allow user to trigger AI parse (e.g. from email list or port call view) and display job status and parsed result (EDD epic § Frontend).

## Scope

- UI to trigger parse for an email (e.g. button "Parse with AI"); call POST /ai/parse with email_id.
- Poll or subscribe to job status (GET /ai/parse/{job_id}); show pending → processing → completed/failed.
- Display parsed result (vessel, port, dates, line items) when completed; show error when failed.
- Optional: link parsed result to port call or create port call from parsed data (if not done in worker).

## Acceptance criteria

- [ ] User can start parse from UI and see status until completion or failure.
- [ ] Parsed data is visible in UI; user can correct or accept (manual override may link to Task 2.10).
- [ ] Loading and error states are clear and tenant-scoped.
