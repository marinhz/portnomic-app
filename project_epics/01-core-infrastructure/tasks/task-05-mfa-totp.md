# Task 1.5 — MFA (TOTP) implementation

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Implement MFA (TOTP) for sensitive roles: challenge after login when required, and store MFA secret encrypted in DB (EDD §6.1, §6.2).

## Scope

- **POST /auth/mfa** — MFA challenge; accepts TOTP code (EDD §7.2).
- MFA secret generated and stored encrypted (key from secret manager).
- Login flow returns `requires_mfa: true` when user has MFA enabled; frontend collects code and calls /auth/mfa.

## Acceptance criteria

- [ ] Users with MFA enabled cannot complete login without valid TOTP.
- [ ] MFA secret encrypted at rest; never logged or returned in API.
- [ ] Invalid TOTP returns clear error; rate limiting applies to MFA attempts.
