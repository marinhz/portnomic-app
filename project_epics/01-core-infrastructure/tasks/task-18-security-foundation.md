# Task 1.18 — Security foundation

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Apply input validation everywhere; ensure no secrets or PII in logs; encrypt MFA secret in DB (EDD §6.1, §6.3).

## Scope

- **Input validation:** Pydantic for all request bodies and query params; reject invalid input with 422 and error envelope.
- **Logging:** Never log passwords, tokens, or full PII; redact in log pipeline if needed (EDD §6.3).
- **MFA secret:** Stored encrypted in DB; encryption key from secret manager (EDD §6.1).

## Acceptance criteria

- [ ] All API inputs validated; no unvalidated user input used in queries or business logic.
- [ ] Logs and error responses contain no passwords, tokens, or unnecessary PII.
- [ ] MFA secrets are encrypted at rest and only decrypted when verifying TOTP.
