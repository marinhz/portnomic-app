# Task 10.4 — Admin AI Settings API & Feature Gating

**Epic:** [10-bring-your-own-ai](../epic.md)  
**Parent:** [Task 10.1](task-01-tenant-llm-config-data-model.md), [Task 10.2](task-02-api-key-storage-encryption.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Expose REST API for company admins to manage LLM config and prompts. Enforce premium plan requirement; return 403 with upgrade CTA for non-premium tenants.

---

## Scope

### 1. Feature gating

- New check: `require_premium_ai(db, tenant_id)` or extend limits service.
- Plans allowed: `professional`, `enterprise`.
- If `starter` (or equivalent): return `403` with `{"code": "upgrade_required", "message": "AI settings are available on Professional and Enterprise plans.", "limit_type": "ai_settings"}`.

### 2. Permission

- Require `company:admin` or equivalent (e.g. `settings:write`).
- Only company admins can configure BYOAI.

### 3. API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/settings/ai` | Get current config (masked; `api_key_configured: bool`) |
| PUT | `/settings/ai` | Create/update config (api_key, base_url, model, enabled) |
| DELETE | `/settings/ai` | Remove config (soft: set enabled=false or delete row) |
| GET | `/settings/ai/prompts` | List prompt overrides (parser_type, prompt_text, version) |
| PUT | `/settings/ai/prompts/{parser_type}` | Set custom prompt |
| POST | `/settings/ai/prompts/{parser_type}/reset` | Reset to default |

### 4. Optional: Test connection

- `POST /settings/ai/test` — Call LLM with minimal prompt to verify key works.
- Returns 200 if OK, 4xx with message if auth/network error.

### 5. Audit logging

- Log `ai_config_updated`, `ai_prompt_updated` (no key values).

---

## Acceptance criteria

- [ ] GET/PUT/DELETE `/settings/ai` work for premium company admins.
- [ ] Non-premium tenants receive 403 with upgrade_required.
- [ ] Non-admin users receive 403.
- [ ] Prompt CRUD endpoints work; reset restores default.
- [ ] API key never returned; only `api_key_configured` boolean.

---

## Related code

- `backend/app/routers/settings.py` or `ai_settings.py` — new router
- `backend/app/services/limits.py` — extend for `require_premium_ai`
- `backend/app/services/tenant_llm_config_svc.py` — CRUD
- `backend/app/services/audit_svc.py` — audit events

---

## Dependencies

- Task 8.2 (Subscription plan) — plan on Tenant
- Task 8.4 (Limits) — feature gating pattern
- Task 10.1, 10.2 — Config model, encryption
