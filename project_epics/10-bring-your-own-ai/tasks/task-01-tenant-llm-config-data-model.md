# Task 10.1 — Tenant LLM Config Data Model

**Epic:** [10-bring-your-own-ai](../epic.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** and **python-project-structure** skills.

---

## Objective

Add a per-tenant LLM configuration entity to store API key, base URL, model, and enabled flag. This is the foundation for BYOAI; actual encryption is handled in Task 10.2.

---

## Scope

### 1. New model: `TenantLlmConfig`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK to Tenant, unique (one config per tenant) |
| `api_key_encrypted` | str | Encrypted; never returned in API |
| `base_url` | str, nullable | OpenAI-compatible base URL; default from platform |
| `model` | str, nullable | Model name; default from platform |
| `enabled` | bool | Default True; allows quick disable without deleting |
| `created_at` | datetime | |
| `updated_at` | datetime | |

### 2. New model: `TenantPromptOverride` (optional in this task)

For prompt management; can be separate table or JSON on TenantLlmConfig:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID | PK |
| `tenant_id` | UUID | FK |
| `parser_type` | enum | `da_email`, `emission_report` |
| `prompt_text` | text | Custom prompt |
| `version` | str | e.g. "v1" |
| `created_at` | datetime | |
| `updated_at` | datetime | |

- Unique: `(tenant_id, parser_type)`.

### 3. Alembic migration

- Create `tenant_llm_configs` table.
- Create `tenant_prompt_overrides` table (or add `prompt_overrides` JSONB to `tenant_llm_configs` if preferred).
- No destructive changes.

### 4. Schemas

- `TenantLlmConfigCreate` — api_key (plain, for input), base_url, model, enabled.
- `TenantLlmConfigUpdate` — partial; api_key optional.
- `TenantLlmConfigResponse` — base_url, model, enabled, **no api_key**; optional `api_key_configured: bool`.

---

## Acceptance criteria

- [ ] `tenant_llm_configs` table exists with correct columns.
- [ ] `tenant_prompt_overrides` (or equivalent) exists for custom prompts.
- [ ] Migration runs cleanly; existing tenants unaffected.
- [ ] Pydantic schemas exclude api_key from responses; support create/update.

---

## Related code

- `backend/app/models/` — new models
- `backend/app/schemas/` — new schemas
- `backend/alembic/versions/` — migration

---

## Dependencies

- Task 1.20 (Multitenant companies) — Tenant model exists
