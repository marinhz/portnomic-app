# Task 1.14 — Auth UI (login, MFA, password reset)

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Login page, MFA challenge flow, and password reset (secure forms); integrate with auth API (EDD §4.1).

## Scope

- Login form: email, password; call POST /auth/login; handle requires_mfa and redirect to MFA step.
- MFA form: TOTP code; call POST /auth/mfa; on success store tokens and redirect to app.
- Password reset: request reset and set new password flows (if in scope for Phase 1).
- Secure forms: no sensitive data in URL or logs; HTTPS in production.

## Acceptance criteria

- [ ] User can log in with email/password and complete MFA when required.
- [ ] Invalid credentials and invalid TOTP show clear messages without leaking security info.
- [ ] On success, tokens are stored and user is redirected to dashboard/app.
