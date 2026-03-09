# Penetration Test Scope and Preparation

**Document Type:** Security — Penetration Testing  
**Source:** ShipFlow AI Engineering Design Document (EDD) §12, §14 (Phase 4)  
**Version:** 1.0  
**Date:** March 2026  
**Classification:** Internal — Security

---

## 1. Scope

### 1.1 In Scope

| Component | Description |
|-----------|-------------|
| **API endpoints** | All REST endpoints under `/api/v1/` (auth, vessels, ports, port-calls, emails, AI parse, admin) |
| **Auth flows** | Login, MFA, refresh token, logout; JWT validation and expiry |
| **Tenant isolation** | Cross-tenant access attempts; IDOR via `tenant_id` manipulation |
| **File / PDF access** | DA PDF generation, storage, download; access control and path traversal |
| **Admin endpoints** | `/api/v1/admin/users`, `/api/v1/admin/roles`; privilege escalation |
| **Webhook endpoints** | `/webhooks/inbound-email`; signature validation, replay, injection |
| **Health / readiness** | `/health`; information disclosure |

### 1.2 Out of Scope

| Component | Reason |
|-----------|--------|
| **Infrastructure / network** | Unless explicitly included (e.g. K8s, load balancer config) |
| **Third-party APIs** | OpenAI, SMTP provider — test integration points only, not provider internals |
| **Social engineering** | Phishing, physical access — separate engagement |
| **DDoS** | DoS testing only with prior approval and limits |

---

## 2. Test Categories

| Category | Focus Areas |
|----------|-------------|
| **Authentication & Authorization** | Brute force, credential stuffing, MFA bypass, JWT tampering, refresh token abuse, privilege escalation |
| **Input Validation** | SQL injection, XSS, command injection, path traversal, oversized payloads, malformed JSON |
| **Tenant Isolation** | Access to other tenants' vessels, port calls, emails, DAs; `tenant_id` in request/response |
| **Rate Limiting** | Bypass, exhaustion, per-endpoint limits (auth vs. API) |
| **Session Management** | Token fixation, concurrent sessions, logout effectiveness, token storage |
| **File Upload / Download** | Malicious file types, path traversal, content-type bypass, access control on PDFs |
| **API Security** | Mass assignment, IDOR, broken object-level authorization (BOLA), excessive data exposure |

---

## 3. Methodology

- **OWASP Top 10** (2021): Broken Access Control, Cryptographic Failures, Injection, Insecure Design, Security Misconfiguration, Vulnerable Components, Auth Failures, Data Integrity Failures, Logging Failures, SSRF.
- **OWASP API Security Top 10** (2023): Broken Object Level Authorization, Broken Authentication, Broken Object Property Level Authorization, Unrestricted Resource Consumption, Broken Function Level Authorization, Unrestricted Access to Sensitive Business Flows, Server Side Request Forgery, Security Misconfiguration, Improper Inventory Management, Unsafe Consumption of APIs.

---

## 4. Findings Template

Use the following template for each finding:

| Field | Description |
|-------|-------------|
| **ID** | PT-YYYY-NNN (e.g. PT-2026-001) |
| **Severity** | Critical / High / Medium / Low |
| **Title** | Short descriptive title |
| **Description** | Detailed description of the vulnerability |
| **Steps to Reproduce** | Numbered steps with request/response examples |
| **Impact** | Business and technical impact |
| **Recommendation** | Remediation steps |
| **Status** | Open / In Progress / Resolved / Accepted Risk |

### Severity Definitions

| Severity | Criteria | Example |
|----------|----------|---------|
| **Critical** | Direct compromise of tenant data, auth bypass, RCE | Cross-tenant data access; JWT secret leak |
| **High** | Significant data exposure, privilege escalation | IDOR to other tenant's DA; MFA bypass |
| **Medium** | Limited impact, requires specific conditions | Information disclosure in error; weak rate limit |
| **Low** | Minimal impact, best practice | Missing security headers; verbose error in dev |

---

## 5. Pre-Test Checklist

| Item | Responsible | Status |
|------|-------------|--------|
| **Environment** | Staging or dedicated pen-test environment; production excluded unless agreed | ☐ |
| **Credentials** | Test accounts: Admin, Operator; MFA disabled or test TOTP for tester | ☐ |
| **Contacts** | Tester POC, internal security lead, escalation path | ☐ |
| **Scope document** | This document signed off; scope and exclusions agreed | ☐ |
| **Data** | Synthetic/demo data only; no real customer data | ☐ |
| **Monitoring** | Alerting configured for pen-test IP/patterns; avoid false positives | ☐ |
| **Backup** | Environment can be restored if needed | ☐ |

---

## 6. Remediation SLA

| Severity | Target Remediation | Notes |
|----------|--------------------|-------|
| **Critical** | 24 hours | Immediate fix or mitigation; may require emergency release |
| **High** | 7 days | Fix in next sprint or hotfix |
| **Medium** | 30 days | Include in planned release |
| **Low** | 90 days | Backlog; address with next security cycle |

*Exceptions: Accepted risk must be documented with business justification and compensating controls.*

---

## 7. API Endpoint Reference

For tester reference, key endpoints (see README and OpenAPI for full list):

| Method | Path | Auth | Notes |
|--------|------|------|-------|
| POST | /api/v1/auth/login | None | Brute force, lockout |
| POST | /api/v1/auth/mfa | MFA token | MFA bypass |
| POST | /api/v1/auth/refresh | Refresh token | Token abuse |
| GET | /api/v1/auth/me | JWT | Token validation |
| GET/POST | /api/v1/vessels | JWT + vessel:* | Tenant isolation |
| GET/POST | /api/v1/port-calls | JWT + port_call:* | Tenant isolation |
| GET/POST | /api/v1/emails | JWT + ai:parse | Tenant isolation |
| POST | /api/v1/ai/parse | JWT + ai:parse | Prompt injection, input validation |
| GET | /api/v1/ai/parse/{job_id} | JWT + ai:parse | IDOR, job_id enumeration |
| POST | /webhooks/inbound-email | Webhook signature | Replay, injection |
| GET/POST | /api/v1/admin/users | JWT + admin:users | Privilege escalation |
| GET/POST | /api/v1/admin/roles | JWT + admin:roles | RBAC bypass |
| GET | /health | None | Info disclosure |

---

## 8. Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | March 2026 | — | Initial pen test scope |

---

*End of Penetration Test Scope*
