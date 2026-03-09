# Task 10.3 — LLM Client Tenant-Aware Routing

**Epic:** [10-bring-your-own-ai](../epic.md)  
**Parent:** [Task 10.1](task-01-tenant-llm-config-data-model.md), [Task 10.2](task-02-api-key-storage-encryption.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Refactor the LLM client and parse worker to use tenant-specific API key, base URL, and model when available. Fall back to platform defaults otherwise.

---

## Scope

### 1. LLM client changes

- `call_llm()` and `parse_email_content()` must accept optional `tenant_id`.
- New internal helper: `_get_llm_config(tenant_id) -> LlmConfig | None`.
  - If tenant has `TenantLlmConfig` with `enabled` → return decrypted key, base_url, model.
  - Else → return platform config from `settings` (current behavior).
- `_build_client()` becomes `_build_client(config: LlmConfig)` — build `AsyncOpenAI` from provided config.

### 2. Prompt resolution

- `get_prompt(parser_type, tenant_id)` — check `TenantPromptOverride` for tenant; else use default from `prompts.py` / emission parser.
- Parse worker passes `tenant_id` into prompt resolution and LLM call.

### 3. Integration points

| Caller | Change |
|--------|--------|
| `parse_worker.process_email` | Pass `tenant_id` to `call_llm` / `parse_email_content` |
| `emission_parser.parse_emission_content` | Pass `tenant_id`; resolve prompt; use tenant config |
| `llm_client.call_llm` | Accept `tenant_id`; resolve config; build client |

### 4. Circuit breaker

- Consider per-tenant circuit breaker or keep global (simpler). Document choice.
- Recommendation: keep global for v1; tenant-specific in future if needed.

### 5. Error handling

- If tenant config exists but key invalid → clear error: "API key invalid or expired. Please update in Settings."
- If no platform key and no tenant key → "AI parsing not configured. Contact your administrator."

---

## Acceptance criteria

- [ ] Parse worker uses tenant LLM config when tenant has BYOAI enabled.
- [ ] Fallback to platform config when tenant has no config.
- [ ] Custom prompts used when tenant has overrides.
- [ ] Errors are tenant-friendly; no key leakage.

---

## Related code

- `backend/app/services/llm_client.py` — tenant-aware routing
- `backend/app/services/parse_worker.py` — pass tenant_id
- `backend/app/services/emission_parser.py` — pass tenant_id, prompt resolution
- `backend/app/services/prompts.py` — extend for tenant overrides

---

## Dependencies

- Task 10.1, 10.2 — Config model and encryption
