# Security Assessment Report — ShipFlow AI

**Task:** 14 — Application Security Audit (Penetration Testing + Code Review)  
**Epic:** 04-beta-security  
**Date:** 2025-03-08  
**Workflow:** `.agents/security.md`  
**Scope:** Backend (FastAPI), Frontend (React), Configuration, OWASP Top 10, Project-Specific Checks

---

## Executive Summary

A comprehensive security assessment was conducted on the ShipFlow AI application per task-14-security-test.md. The review covered source code security audit, OWASP Top 10 mapping, project-specific multi-tenancy and admin checks, and dependency scanning.

**Overall Risk Level:** **Medium** — Several previously remediated critical items are in place; remaining findings are primarily Medium and Low. No running application was available for live penetration testing; static analysis and code review findings are documented below.

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High | 2 |
| Medium | 5 |
| Low | 3 |
| Info | 3 |

---

## 1. Vulnerability List

### V1: Default Secrets in Non-Production Environments

- **Severity:** High  
- **Location:** `backend/app/config.py:11,16`  
- **Description:** `jwt_secret` and `mfa_encryption_key` default to `"change-me"`. Production is protected by `@model_validator` that fails fast, but development/staging deployments may run with these defaults. If a staging environment is exposed or misconfigured as production, attackers could forge JWTs and decrypt MFA secrets.  
- **Reproduction:** Deploy with `ENVIRONMENT=development` and omit `JWT_SECRET` / `MFA_ENCRYPTION_KEY`; application starts with default secrets.  
- **Impact:** JWT forgery, MFA bypass, session hijacking in non-production environments.  
- **Remediation:** Add a startup warning when default secrets are used; consider failing in staging as well. Document in deployment guide that all environments must set strong secrets.  
- **References:** OWASP A02 Cryptographic Failures, A05 Security Misconfiguration  

---

### V2: Refresh Token Endpoint Not Rate Limited

- **Severity:** High  
- **Location:** `backend/app/routers/auth.py:181-214`  
- **Description:** The `/api/v1/auth/refresh` endpoint has no rate limiter. Login and MFA use `auth_limiter.limit()`, but refresh does not. An attacker with a stolen refresh token (or brute-forcing if token format were weak) could abuse the endpoint.  
- **Reproduction:** Call `POST /api/v1/auth/refresh` repeatedly with a valid refresh token; no 429 response.  
- **Impact:** Token abuse, potential brute-force if token entropy is low; no throttling on refresh abuse.  
- **Remediation:** Apply `auth_limiter.limit()` to the refresh endpoint (e.g. same as login: `rate_limit_auth_per_minute`).  
- **References:** OWASP A04 Insecure Design, A07 Auth Failures  

---

### V3: Unauthenticated GDPR Processing Records Endpoint

- **Severity:** Medium  
- **Location:** `backend/app/routers/gdpr.py:257-262`  
- **Description:** `GET /api/v1/gdpr/processing-records` has no authentication. It returns static GDPR Article 30 processing records (generic compliance text). While the data is non-sensitive, unauthenticated endpoints expand the attack surface.  
- **Reproduction:** `curl https://api.example.com/api/v1/gdpr/processing-records` without Authorization header; returns 200 with data.  
- **Impact:** Information disclosure (low—static compliance text); inconsistent auth model.  
- **Remediation:** Add `Depends(get_current_user)` or `RequirePermission("*")` for consistency. If intentionally public for compliance pages, document and consider a separate public route.  
- **References:** OWASP A01 Broken Access Control  

---

### V4: Role Update Allows Self-Privilege Escalation Within Tenant

- **Severity:** Medium  
- **Location:** `backend/app/services/admin.py:114-126`, `backend/app/schemas/admin.py:34-39`  
- **Description:** `RoleUpdate` accepts `permissions: list[str] | None`. A user with `admin:roles` can update any role in their tenant, including their own, to add permissions such as `admin:users`, `*`, or `billing:manage`. This is tenant-scoped but allows horizontal privilege escalation within the tenant.  
- **Reproduction:** As a tenant admin with `admin:roles`, update own role to add `admin:users`; gain user management.  
- **Impact:** Tenant admins can escalate their own permissions; design may be intentional for small tenants.  
- **Remediation:** Consider restricting role updates so a user cannot add permissions they do not already have, or require a separate "super admin" role for role changes. Document as accepted risk if intentional.  
- **References:** OWASP A01 Broken Access Control  

---

### V5: Token Storage in sessionStorage (XSS Exposure)

- **Severity:** Medium  
- **Location:** `frontend/src/api/client.ts:12-31`  
- **Description:** Access and refresh tokens are stored in `sessionStorage`. Any XSS vulnerability could allow an attacker to read tokens via `sessionStorage.getItem()`.  
- **Reproduction:** Inject script via stored XSS; exfiltrate `sessionStorage.getItem("sf_at")` and `sessionStorage.getItem("sf_rt")`.  
- **Impact:** Token theft, account takeover if XSS exists.  
- **Remediation:** Prefer in-memory storage for access token; use httpOnly cookie for refresh token. sessionStorage is acceptable for MVP but should be migrated for higher assurance.  
- **References:** OWASP A07 Auth Failures  

---

### V6: No Refresh Token Rotation

- **Severity:** Medium  
- **Location:** `backend/app/routers/auth.py:181-214`, `backend/app/services/auth.py:51-72`  
- **Description:** Refresh endpoint returns only a new access token; the refresh token is not rotated. A stolen refresh token remains valid until expiry (10080 minutes by default).  
- **Reproduction:** Steal refresh token; use it repeatedly until expiry.  
- **Impact:** Long-lived token reuse; no detection of token theft.  
- **Remediation:** Implement refresh token rotation: issue new refresh token on each use, invalidate previous. Consider token binding (e.g. fingerprint).  
- **References:** OWASP A07 Auth Failures  

---

### V7: Tenant LLM base_url Not Validated for SSRF

- **Severity:** Medium  
- **Location:** `backend/app/services/llm_client.py`, `backend/app/schemas/tenant_llm_config.py:14,22`  
- **Description:** Tenant AI settings allow `base_url` to be set. The LLM client uses this URL when calling external APIs. If a tenant configures `base_url` to an internal address (e.g. `http://169.254.169.254/`, `http://localhost:6379/`), the backend could be used for SSRF.  
- **Reproduction:** As tenant admin, set `base_url` to `http://169.254.169.254/latest/meta-data/`; trigger AI parse; backend may fetch cloud metadata.  
- **Impact:** SSRF to internal services, cloud metadata, or other internal resources.  
- **Remediation:** Validate `base_url` against an allowlist of known LLM API hosts (e.g. `api.openai.com`, `api.groq.com`), or block private IP ranges and localhost.  
- **References:** OWASP A10 SSRF  

---

### V8: Billing success_url / cancel_url Open Redirect Risk

- **Severity:** Low  
- **Location:** `backend/app/routers/billing.py:31-34, 58-82`  
- **Description:** `CreateCheckoutSessionRequest` accepts `success_url` and `cancel_url` from the client. These are passed to Stripe Checkout. Stripe may validate URLs, but if misconfigured, could enable open redirect after payment.  
- **Reproduction:** Pass `success_url=https://evil.com/phish`; user may be redirected there after checkout.  
- **Impact:** Phishing, open redirect if Stripe does not enforce allowlist.  
- **Remediation:** Validate `success_url` and `cancel_url` against an allowlist (e.g. same origin or configured frontend domain) before passing to Stripe.  
- **References:** OWASP A01 Broken Access Control  

---

### V9: Storage blob_id Path Traversal (Defense in Depth)

- **Severity:** Low  
- **Location:** `backend/app/services/storage.py:39-42`  
- **Description:** `_get_local(blob_id)` uses `Path(settings.storage_local_path) / blob_id` without validating `blob_id`. Currently `blob_id` is only from `store_blob` (UUID-based) or from DB (`da.pdf_blob_id`). If a future endpoint accepts user-supplied `blob_id`, path traversal (e.g. `../../../etc/passwd`) could occur.  
- **Reproduction:** Hypothetical: if an endpoint accepted `blob_id` from query param, pass `blob_id=../../../etc/passwd`.  
- **Impact:** Low currently (blob_id is internal); potential LFI if API is extended.  
- **Remediation:** Validate `blob_id` format (e.g. UUID + extension, no `..`, no path separators). Use `Path.resolve()` and ensure result is under `storage_local_path`.  
- **References:** OWASP A01 Broken Access Control  

---

### V10: No Content-Security-Policy Header

- **Severity:** Low  
- **Location:** `backend/app/middleware/security_headers.py`, `frontend/index.html`  
- **Description:** Security headers include `X-Content-Type-Options`, `X-Frame-Options`, and HSTS (production), but no `Content-Security-Policy`. Frontend has no CSP meta tag or header.  
- **Reproduction:** Inspect response headers; no CSP present.  
- **Impact:** Reduced protection against XSS, inline script injection.  
- **Remediation:** Add CSP header (or meta tag for static HTML) with appropriate directives (e.g. `default-src 'self'`, `script-src 'self'`, `style-src 'self' 'unsafe-inline'` for Tailwind).  
- **References:** OWASP A05 Security Misconfiguration  

---

### V11: Webhook Development Bypass (Documented)

- **Severity:** Info  
- **Location:** `backend/app/routers/webhooks.py:33-44`  
- **Description:** When `webhook_inbound_secret` is empty and `environment != "production"`, `_verify_signature` returns `True`, accepting unverified webhooks. This is intentional for local development.  
- **Remediation:** Ensure development/staging are never exposed to the internet with this config. Document in deployment guide.  
- **References:** OWASP A08 Data Integrity  

---

### V12: JWT Secret Minimum Length Not Enforced

- **Severity:** Info  
- **Location:** `backend/app/config.py`  
- **Description:** Production blocks default `"change-me"`, but does not enforce minimum length (e.g. 32 bytes for HS256). A weak but non-default secret could be used.  
- **Remediation:** Add validation: in production, require `len(jwt_secret.encode()) >= 32`.  
- **References:** OWASP A02 Cryptographic Failures  

---

### V13: Platform Admin Configuration

- **Severity:** Info  
- **Location:** `backend/app/config.py:19`, `backend/app/dependencies/platform.py`  
- **Description:** Platform admin access is granted via `platform_admin_emails` (comma-separated). If empty, no one can access platform endpoints. Must be correctly set in production.  
- **Remediation:** Document required env var; add startup check in production that at least one platform admin is configured if platform routes are used.  
- **References:** OWASP A05 Security Misconfiguration  

---

## 2. OWASP Top 10 Mapping

| Risk | Status | Notes |
|------|--------|------|
| **A01 Broken Access Control** | Partial | Tenant isolation verified; processing-records unauthenticated (V3); role self-escalation (V4); billing URL validation (V8) |
| **A02 Cryptographic Failures** | Good | bcrypt for passwords; Fernet for MFA/API keys; production blocks default secrets; JWT secret length not enforced (V12) |
| **A03 Injection** | Good | SQLAlchemy ORM; parameterized `text()` in email_service; Pydantic validation on inputs; no raw SQL concatenation |
| **A04 Insecure Design** | Partial | Auth rate limiting on login/MFA; refresh not rate limited (V2) |
| **A05 Security Misconfiguration** | Partial | Security headers present; docs disabled in prod; CORS configurable; no CSP (V10); default secrets in dev (V1) |
| **A06 Vulnerable Components** | Good | npm audit: 0 vulnerabilities; pip-audit not run (pip audit unavailable); setuptools upgraded per prior audit |
| **A07 Auth Failures** | Partial | Strong password hashing; MFA; JWT type validation; sessionStorage tokens (V5); no refresh rotation (V6); refresh not rate limited (V2) |
| **A08 Data Integrity** | Good | Webhook signature verification (prod); Stripe webhook verification; OAuth state encryption |
| **A09 Logging Failures** | Good | Sensitive headers excluded; JWT claims decoded for context only, not logged; no passwords/tokens in logs |
| **A10 SSRF** | Partial | Tenant LLM base_url not validated (V7); OAuth uses fixed provider URLs |

---

## 3. Project-Specific Checks

### Multi-Tenancy

- **Status:** Verified  
- All tenant-scoped services use `tenant_id` from `get_tenant_id` (JWT). Queries consistently filter by `tenant_id` in admin, email, vessel, tariff, port, DA, GDPR, integrations, emissions, AI, and AI settings. No cross-tenant data leakage identified.

### Admin Endpoints

- **Status:** Verified  
- Admin routes require `RequirePermission("admin:users")` or `RequirePermission("admin:roles")`. Platform routes require `get_platform_admin` (email in `platform_admin_emails`).

### Secrets Handling

- **Status:** Partial  
- Production fails fast on default JWT/MFA secrets. `.env` loading from `../.env` and `.env`. Ensure `.env` is in `.gitignore` at repo root (per prior audit F9). No `.env.example` with placeholders found at project root.

---

## 4. Penetration Testing

**Note:** No running application was available for live penetration testing. The following would be tested against a staging environment:

### Authentication & Session Management

- Brute force protection on `/login` and `/mfa` (rate limited)
- Session hijacking (token in Authorization header; sessionStorage)
- Token expiration and reuse (access 15 min; refresh 10080 min; no rotation)
- Refresh endpoint rate limiting (missing—V2)

### Authorization

- Role escalation (admin:roles can modify own role—V4)
- Horizontal access (tenant_id in all queries—verified)
- Vertical access (platform admin required for tenant management)

### Injection

- SQL injection (parameterized queries—no vectors found)
- Command injection (no shell execution of user input)
- Template injection (no user-controlled templates)

### Client-Side

- XSS (no `dangerouslySetInnerHTML`; React escapes by default)
- CSP (missing—V10)

### Request Forgery

- CSRF (API uses Bearer token; no cookie-based auth for state-changing ops; SameSite not applicable for token-based API)

### File Upload

- No direct file upload endpoints; PDFs generated server-side; blob storage uses UUID-based IDs

### API Attacks

- Mass assignment (Pydantic schemas with explicit fields; no `model_dump(exclude_unset=True)` on arbitrary input)
- Rate limiting (global + auth-specific; refresh not limited—V2)
- Error exposure (production hides exception details—main.py:96-98)

### Security Headers

- X-Content-Type-Options: nosniff ✓  
- X-Frame-Options: DENY ✓  
- Strict-Transport-Security (production) ✓  
- Content-Security-Policy ✗ (V10)

---

## 5. Dependency Audit

| Tool | Result |
|------|--------|
| `npm audit` (frontend) | 0 vulnerabilities |
| `pip audit` | Not available (pip 22.3.1); `pip-audit` install failed |
| Prior audit (docs/security-audit-2025-03.md) | setuptools upgraded; ecdsa CVE-2024-23342 mitigated (HS256 used, not ECDSA) |

**Recommendation:** Run `pip-audit` or `safety check` in CI; upgrade pip and retry in a clean environment.

---

## 6. Security Risk Summary

- **Overall Risk Level:** Medium  
- **Critical Areas:**
  1. **Auth hardening:** Rate limit refresh endpoint (V2); implement refresh token rotation (V6)
  2. **Secrets:** Enforce JWT secret length in production (V12); ensure all environments use strong secrets (V1)
  3. **SSRF:** Validate tenant LLM base_url (V7)

- **Strengths:**
  - Tenant isolation consistently enforced
  - Admin and platform endpoints properly protected
  - Input validation via Pydantic
  - No SQL injection vectors
  - Webhook and Stripe signature verification
  - Sensitive data redacted from logs

---

## 7. Remediation Recommendations

### Secure Coding

1. Add rate limiting to `/auth/refresh`
2. Implement refresh token rotation
3. Validate tenant LLM `base_url` against allowlist; block private IPs
4. Add `blob_id` validation in storage (format, no `..`)
5. Restrict role self-escalation or document as accepted risk

### Configuration

1. Add CSP header (or meta tag) with appropriate directives
2. Validate billing `success_url` / `cancel_url` against allowlist
3. Require JWT secret length ≥ 32 bytes in production
4. Add startup check for platform admin when platform routes are used

### Infrastructure

1. Ensure `.env` in `.gitignore`; never commit secrets
2. Run `pip-audit` or `safety check` in CI
3. Consider httpOnly cookie for refresh token (requires backend cookie support)

---

## Appendix: Prior Audit Findings (March 2025)

The following were remediated in `docs/security-audit-2025-03.md`:

- F1: Default secrets in production → Fail-fast validator added
- F2: Webhook unverified in production → Returns False when secret empty in prod
- F3: Missing security headers → SecurityHeadersMiddleware added
- F4: setuptools CVEs → Upgraded to ≥78.1.1
- F5: CORS → No change needed

Remaining from prior audit (documented, not fixed):

- F6: sessionStorage tokens (this report V5)
- F7: Refresh token rotation (this report V6)
- F8: ecdsa CVE (mitigated—HS256 used)
- F9: .gitignore for .env
- F10: JWT secret strength (this report V12)
