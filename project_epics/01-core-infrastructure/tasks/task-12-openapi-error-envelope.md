# Task 1.12 — OpenAPI spec and error envelope

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Publish OpenAPI 3.0 spec and enforce consistent error response envelope across the API (EDD §7.1).

## Scope

- **Error envelope:** `{ "error": { "code", "message", "details" } }` for all error responses (EDD §7.1).
- OpenAPI document generated from FastAPI (or maintained separately); available at e.g. `/openapi.json` or `/docs`.
- Versioning: URL prefix `/api/v1/` (EDD §7.1).

## Acceptance criteria

- [ ] All 4xx/5xx responses use the standard error envelope.
- [ ] OpenAPI spec is valid and describes auth, endpoints, and schemas; no sensitive data in examples.
- [ ] API versioning is clear in path or docs.
