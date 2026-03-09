# Task 1.22 — Web Application Security Audit & Remediation

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Perform a comprehensive security analysis of the ShipFlow web application (backend + frontend) and fix any security vulnerabilities found. Use the **Web Application Security Specialist** agent for systematic review and remediation.

---

## Problem statement

- **Current state:** The application has auth (JWT, MFA), RBAC, tenant isolation, and input validation (Task 1.18). No formal security audit has been performed.
- **Risk:** Undetected vulnerabilities (OWASP Top 10, misconfigurations, secrets exposure) could lead to data breaches, privilege escalation, or cross-tenant access.
- **Goal:** Identify and remediate security issues before production; establish a baseline for ongoing security reviews.

---

## Scope

### 1. Backend (FastAPI)

- **Authentication & JWT:** Token handling, expiry, algorithm, secret strength, refresh flow, token storage.
- **Authorization:** RBAC enforcement, permission checks, tenant isolation (no cross-tenant data leakage).
- **Input validation:** Pydantic schemas, SQL injection prevention, path traversal, mass assignment.
- **Secrets & config:** No hardcoded secrets; env vars; sensitive data in logs (passwords, tokens, PII).
- **HTTP security:** CORS, CSP, headers (X-Frame-Options, X-Content-Type-Options, etc.), HTTPS enforcement.
- **Rate limiting:** Auth endpoints, API endpoints; brute-force protection.
- **Dependencies:** Known vulnerabilities in Python packages (e.g. `pip audit`, safety).

### 2. Frontend (React)

- **XSS:** User input rendering, `dangerouslySetInnerHTML`, URL params, localStorage/sessionStorage.
- **Auth storage:** Token storage (memory vs localStorage vs httpOnly cookie); exposure risk.
- **API client:** Credentials handling, error messages (no sensitive data leakage).
- **Dependencies:** Known vulnerabilities in npm packages (`npm audit`).

### 3. Infrastructure & config

- **Environment:** Default secrets (e.g. `jwt_secret: "change-me"`), `.env` handling, `.gitignore`.
- **Database:** Connection strings, migrations, SQL injection vectors.
- **Redis:** Session storage, idempotency keys; no sensitive data in keys/values.

---

## Acceptance criteria

- [x] Security audit completed; findings documented (severity: Critical, High, Medium, Low, Info).
- [x] All Critical and High findings remediated (or explicitly accepted with mitigation plan).
- [x] Medium findings addressed or documented with risk acceptance.
- [x] No hardcoded secrets; sensitive config from env or secret manager.
- [x] Dependency audit run; no known Critical/High CVEs in production dependencies.
- [x] Security headers configured (CORS, CSP, X-Frame-Options, etc.).
- [x] Audit report or checklist stored for future reference (e.g. `docs/security-audit-YYYY-MM.md`).

---

## Implementation notes

### Agent usage

Use the **Web Application Security Specialist** agent (`.agents/security.md`):

1. **Analyze** — Run through OWASP Top 10 and project-specific checks.
2. **Document** — List findings with severity, location, and remediation steps.
3. **Fix** — Apply fixes for Critical/High; propose patches for Medium/Low.
4. **Verify** — Re-check after fixes; ensure no regressions.

### OWASP Top 10 (2021) quick reference

| # | Risk | ShipFlow focus |
|---|------|----------------|
| A01 | Broken Access Control | RBAC, tenant isolation, admin endpoints |
| A02 | Cryptographic Failures | JWT secret, MFA encryption, HTTPS |
| A03 | Injection | SQL, NoSQL, command; Pydantic validation |
| A04 | Insecure Design | Auth flow, multi-tenancy design |
| A05 | Security Misconfiguration | CORS, headers, default creds |
| A06 | Vulnerable Components | pip/npm audit |
| A07 | Auth Failures | Login, MFA, session, JWT |
| A08 | Data Integrity | Webhooks, state, CSRF |
| A09 | Logging Failures | PII/secrets in logs |
| A10 | SSRF | External URLs, webhooks |

### Key files to review

- `backend/app/dependencies/auth.py` — JWT validation
- `backend/app/config.py` — Secrets, defaults
- `backend/app/main.py` — CORS, middleware, rate limiting
- `backend/app/routers/*.py` — Auth, RBAC, input handling
- `frontend/src/**` — Token storage, XSS vectors, API client
- `.env.example` — Required vs optional; no real secrets

---

## Related code

- `backend/app/dependencies/auth.py` — JWT, current user
- `backend/app/dependencies/platform.py` — Platform admin
- `backend/app/main.py` — App setup, CORS, middleware
- `backend/app/config.py` — Settings, secrets
- `frontend/src/lib/api.ts` (or equivalent) — API client, auth
- `frontend/src/pages/auth/*` — Login, MFA forms

---

## Dependencies

- Task 1.18 (Security foundation) — Input validation, logging, MFA encryption.
- Task 1.6 (Tenant middleware), 1.7 (RBAC) — Access control.
- Task 1.4 (Auth service), 1.5 (MFA) — Authentication.
