# Task 10.2 — API Key Storage & Encryption

**Epic:** [10-bring-your-own-ai](../epic.md)  
**Parent:** [Task 10.1 — Tenant LLM config data model](task-01-tenant-llm-config-data-model.md)

---

## Agent

Use the **Backend** agent ([`.agents/backend.md`](../../../.agents/backend.md)) with **fastapi-python** skill.

---

## Objective

Implement secure encryption and decryption of tenant API keys at rest. Keys must never appear in logs, API responses, or error messages.

---

## Scope

### 1. Encryption service

- `backend/app/services/encryption.py` (or use existing if present).
- **Algorithm:** Fernet (symmetric) or AES-256-GCM.
- **Key source:** `ENCRYPTION_KEY` or `LLM_KEY_ENCRYPTION_KEY` from config/env; 32 bytes for Fernet.
- Functions: `encrypt_api_key(plain: str) -> str`, `decrypt_api_key(encrypted: str) -> str`.

### 2. Integration with TenantLlmConfig

- On create/update: encrypt `api_key` before storing in `api_key_encrypted`.
- On read for LLM calls: decrypt only when building client; never expose in API response.
- If decryption fails: log generic error; treat as "key invalid" (do not log key material).

### 3. Key rotation (optional)

- Document how to rotate `ENCRYPTION_KEY` (re-encrypt all keys with new key).
- Defer full implementation if time-boxed.

### 4. Security checklist

- [x] Keys never in `logger.info/debug` or exception messages.
- [x] Response schemas never include `api_key` or decrypted value.
- [x] Optional: mask in logs as `sk-...xxxx` if key ID is logged for debugging.

---

## Acceptance criteria

- [x] `encrypt_api_key` / `decrypt_api_key` work correctly.
- [x] TenantLlmConfig service encrypts on save, decrypts only for LLM client.
- [x] No key material in logs or API responses.

---

## Related code

- `backend/app/services/encryption.py` — new or extended
- `backend/app/config.py` — add `llm_key_encryption_key`
- `backend/app/services/tenant_llm_config_svc.py` — use encryption in CRUD

---

## Dependencies

- Task 10.1 — TenantLlmConfig model exists
