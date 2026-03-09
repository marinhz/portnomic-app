# ShipFlow AI — Engineering Design Document

**Document Type:** Engineering Design Document (EDD)  
**Source:** SHIPFLOW AI Enterprise Technical Specification v3.0  
**Version:** 1.0  
**Date:** March 2026  
**Classification:** Confidential — Architecture & Engineering

---

## Table of Contents

1. [Document Purpose & Scope](#1-document-purpose--scope)
2. [System Context & Requirements](#2-system-context--requirements)
3. [Architecture Overview](#3-architecture-overview)
4. [Component Design](#4-component-design)
5. [Data Model & Persistence](#5-data-model--persistence)
6. [Security Design](#6-security-design)
7. [API Design & Integration](#7-api-design--integration)
8. [AI Processing Pipeline](#8-ai-processing-pipeline)
9. [DA Generator & Financial Workflow](#9-da-generator--financial-workflow)
10. [DevOps, Deployment & Infrastructure](#10-devops-deployment--infrastructure)
11. [Observability & Resilience](#11-observability--resilience)
12. [Threat Model & Risk Mitigation](#12-threat-model--risk-mitigation)
13. [Compliance & GDPR](#13-compliance--gdpr)
14. [Implementation Roadmap](#14-implementation-roadmap)
15. [Appendices](#15-appendices)

---

## 1. Document Purpose & Scope

### 1.1 Purpose

This Engineering Design Document (EDD) translates the ShipFlow AI Enterprise Technical Specification into an implementable technical blueprint. It is intended for:

- **Software architects** — system structure, boundaries, and integration points  
- **Backend / frontend engineers** — component contracts, data flows, and API contracts  
- **DevOps / SRE** — deployment topology, scaling, and observability  
- **Security engineers** — controls, threat mitigation, and compliance mapping  

### 1.2 Scope

| In scope | Out of scope |
|----------|--------------|
| Multi-tenant SaaS platform for maritime agency operations | Third-party LLM provider selection (treated as pluggable) |
| Email → structured data via AI, DA generation, RBAC, audit | Detailed UI wireframes and UX copy |
| Cloud-native deployment (Docker, Kubernetes), CI/CD | Legal/commercial terms and SLAs |
| Security-by-design, GDPR-aligned controls | Hardware or physical infrastructure procurement |

### 1.3 Definitions

| Term | Definition |
|------|------------|
| **DA** | Disbursement Account — port expense statement for a vessel call |
| **Port call** | A vessel’s visit to a port; unit of work for DA generation |
| **Tenant** | Isolated organization (e.g. agency) in the multi-tenant system |
| **Proforma DA** | Preliminary DA before final approval and dispatch |

---

## 2. System Context & Requirements

### 2.1 Business Context

The maritime agency domain is characterized by:

- High volume of **email-based** operational communication  
- **Manual** data entry and calculation for port expenses  
- **Strict** financial and compliance requirements  
- Need for **transparency** toward shipowners  

ShipFlow AI targets:

- **40–60%** reduction in operational workload  
- **Lower** financial and compliance risk  
- **Real-time** visibility over vessels and disbursements  

### 2.2 Functional Requirements (Summary)

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1 | Ingest operational emails (IMAP/API) and associate with tenant/vessel/port call | Must |
| FR-2 | Extract structured maritime data from emails via AI (vessel, port, dates, amounts, line items) | Must |
| FR-3 | Store and version port-specific tariff configurations | Must |
| FR-4 | Generate Proforma and Final DA using configurable formula engine | Must |
| FR-5 | Export DA as PDF and support automated email dispatch | Must |
| FR-6 | Enforce role-based access (RBAC) and tenant isolation on all resources | Must |
| FR-7 | Support MFA and short-lived JWT authentication | Must |
| FR-8 | Maintain immutable audit logs for security and compliance | Must |
| FR-9 | Support data export and erasure for GDPR | Should |

### 2.3 Non-Functional Requirements

| ID | NFR | Target / Constraint |
|----|-----|---------------------|
| NFR-1 | Availability | 99.5% (excluding planned maintenance) |
| NFR-2 | API latency (p95) | < 500 ms for read endpoints |
| NFR-3 | AI parse latency (p95) | < 30 s per email (depends on LLM) |
| NFR-4 | Multi-tenancy | Strict data isolation; no cross-tenant access |
| NFR-5 | Security | AES-256 at rest, TLS 1.3 in transit |
| NFR-6 | Audit | All sensitive actions logged; logs immutable and SIEM-ready |

---

## 3. Architecture Overview

### 3.1 Layered Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                                    │
│  React.js SPA │ Auth (JWT/MFA) │ Tenant context │ Responsive UI          │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     APPLICATION LAYER                                    │
│  FastAPI │ REST/OpenAPI 3.0 │ Tenant middleware │ RBAC │ Rate limiting   │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
          ┌───────────────────────────┼───────────────────────────┐
          ▼                           ▼                           ▼
┌──────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐
│   DATA LAYER     │    │  AI PROCESSING       │    │  MESSAGE / CACHE      │
│  PostgreSQL      │    │  LLM integration     │    │  Redis (cache/queue)  │
│  (primary +      │    │  Email parsing       │    │  Background jobs      │
│   read replicas) │    │  Structured output   │    │  (Celery/ARQ)         │
└──────────────────┘    └──────────────────────┘    └──────────────────────┘
          │                           │                           │
          └───────────────────────────┼───────────────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     INFRASTRUCTURE LAYER                                 │
│  Docker │ Kubernetes │ Terraform │ CI/CD (GitHub Actions / GitLab CI)    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Principles

- **Separation of concerns** — Presentation, application, data, and AI processing are clearly bounded.  
- **API-first** — All capabilities exposed via REST; OpenAPI 3.0 as single source of truth.  
- **Cloud-native** — Stateless app services, horizontal scaling, externalized state (DB, cache, queue).  
- **Observability first** — Metrics, structured logs, and traces designed in from the start.

### 3.3 Multi-Tenancy Model

- **Tenant identifier:** `tenant_id` (UUID) on all tenant-scoped entities.  
- **Isolation:** Every API request resolved to a tenant (via JWT or context); all queries filtered by `tenant_id`.  
- **No cross-tenant access** — enforced at middleware and repository layer; no shared caches keyed without `tenant_id`.

---

## 4. Component Design

### 4.1 Presentation Layer (Frontend)

| Component | Responsibility | Tech |
|-----------|----------------|------|
| App shell | Routing, auth state, tenant context, layout | React 18+, React Router |
| Auth UI | Login, MFA challenge, password reset | React, secure forms |
| Dashboard | Vessels, port calls, DA list, KPIs | React, data tables, charts |
| Vessel / Port call | CRUD and detail views | React, forms |
| DA workspace | Proforma/Final DA view, approve, PDF, send | React, PDF preview |
| Admin | User/role management (tenant-scoped) | React, RBAC-driven UI |
| API client | HTTP client, JWT attach, refresh, error handling | Axios/fetch + interceptors |

**Design decisions:**

- SPA with hash or browser history routing; auth tokens in memory + optional httpOnly cookie for refresh.  
- No tenant_id in URL; tenant comes from authenticated user.  
- All API calls go through a single client that adds `Authorization: Bearer <access_token>` and handles 401 (refresh or re-login).

### 4.2 Application Layer (Backend)

| Component | Responsibility | Tech |
|-----------|----------------|------|
| API gateway | Routing, CORS, rate limiting, request ID | FastAPI |
| Auth service | Login, MFA, JWT issue/validate, refresh | FastAPI, PyJWT, MFA lib |
| Tenant middleware | Resolve tenant from JWT; inject into request context | FastAPI dependency |
| RBAC middleware | Check permission for (user, resource, action) | FastAPI dependency |
| Vessel service | CRUD vessels (tenant-scoped) | FastAPI, service + repository |
| Port call service | CRUD port calls, link to vessel | FastAPI, service + repository |
| Email ingest service | Receive email (IMAP/webhook), enqueue for AI | FastAPI, queue producer |
| AI orchestration | Request AI parse, map result to domain entities | FastAPI, internal client to AI service |
| DA service | Create/update Proforma and Final DA, run formula engine | FastAPI, service + repository |
| PDF / notification | Generate DA PDF, send email | FastAPI, background job trigger |
| Admin service | User/role CRUD (tenant-scoped) | FastAPI, service + repository |
| Audit logger | Write immutable audit events | FastAPI, append-only store |

**Design decisions:**

- One FastAPI application; modules by domain (auth, vessels, port_calls, da, ai, admin).  
- Tenant and RBAC enforced in dependencies; services assume tenant and user are set.  
- Long-running work (AI parse, PDF generation, email send) offloaded to background workers.

### 4.3 Data Layer

- **Primary store:** PostgreSQL (ACID, tenant-scoped tables with `tenant_id`).  
- **Migrations:** Versioned schema migrations (e.g. Alembic); no destructive changes without explicit flow.  
- **Read scaling:** Read replicas for reporting and read-heavy endpoints; write to primary only.  
- **Caching:** Redis for session and idempotency keys; optional cache-aside for reference data (ports, tariffs) keyed by `tenant_id`.

### 4.4 AI Processing Layer

- **Input:** Raw email (headers + body), optional metadata (vessel_id, port_call_id).  
- **Output:** Structured payload (vessel ref, port, dates, line items, amounts, currency).  
- **Integration:** Pluggable LLM client (OpenAI-compatible API); prompts and output schema versioned.  
- **Orchestration:** Backend enqueues job; worker calls LLM, validates output, persists to DB and links to port call/vessel.  
- **Idempotency:** Same email_id not processed twice; idempotency key in queue/DB.

### 4.5 Infrastructure Layer

- **Compute:** Kubernetes; backend and workers as Deployments; HPA for CPU/memory or custom metrics.  
- **Networking:** Ingress (TLS termination), internal service mesh optional.  
- **Secrets:** Kubernetes Secrets or external secret manager; never in code or image.  
- **IaC:** Terraform for cluster, DB, Redis, DNS, and environment separation (dev/staging/prod).

---

## 5. Data Model & Persistence

### 5.1 Core Entities (Logical)

- **Tenant** — Id, name, slug, settings (e.g. timezone), created_at.  
- **User** — Id, tenant_id, email, password_hash, mfa_secret (encrypted), role_id, created_at, last_login_at.  
- **Role** — Id, tenant_id, name, permissions (JSON or relation).  
- **Vessel** — Id, tenant_id, name, IMO, MMSI, type, other attributes, created_at.  
- **Port** — Id, tenant_id (or global), name, code, country, timezone.  
- **PortCall** — Id, tenant_id, vessel_id, port_id, eta, etd, status, created_at.  
- **Email** — Id, tenant_id, port_call_id (nullable), external_id, subject, body_text, body_html, received_at, processing_status, ai_raw_output (JSON), created_at.  
- **Tariff** — Id, tenant_id, port_id, name, version, formula_config (JSON), valid_from, valid_to.  
- **DisbursementAccount (DA)** — Id, tenant_id, port_call_id, version, type (proforma|final), status (draft|pending_approval|approved|sent), line_items (JSON or relation), totals, pdf_blob_id (nullable), created_at, approved_at, sent_at.  
- **AuditLog** — Id, tenant_id, user_id, action, resource_type, resource_id, payload (JSON), ip, user_agent, created_at.

### 5.2 Key Relationships

- User N:1 Tenant, N:1 Role.  
- Vessel N:1 Tenant.  
- PortCall N:1 Vessel, N:1 Port; Tenant via Vessel/Port.  
- Email N:1 Tenant; N:1 PortCall (optional).  
- DA N:1 PortCall; N:1 Tenant.  
- AuditLog N:1 Tenant, N:1 User.

### 5.3 Indexing Strategy

- All tenant-scoped tables: composite index `(tenant_id, <main_lookup>)` (e.g. `tenant_id, created_at`, `tenant_id, port_call_id`).  
- Email: `(tenant_id, external_id)` unique; `(tenant_id, processing_status)` for queue consumers.  
- AuditLog: `(tenant_id, created_at)`, `(resource_type, resource_id)` for compliance queries.

### 5.4 Retention & Archive

- Operational data: per tenant policy (e.g. 7 years for financial records).  
- Audit logs: immutable; retention per compliance (e.g. 7 years); archive to cold storage if needed.  
- Emails: retain raw and parsed for dispute resolution; align with GDPR and retention policy.

---

## 6. Security Design

### 6.1 Encryption

| Where | Mechanism |
|-------|-----------|
| Data at rest | AES-256 (DB encryption and/or application-level for PII/sensitive fields) |
| Data in transit | TLS 1.3 only; HSTS; certificate lifecycle managed |
| Secrets | Stored in secret manager; never logged or in client payloads |
| MFA secret | Encrypted in DB with key from secret manager |

### 6.2 Authentication & Access Control

- **Authentication:** Login with email + password; MFA (TOTP) required for sensitive roles.  
- **Tokens:** JWT access (short-lived, e.g. 15 min), refresh token (longer, stored server-side or in httpOnly cookie).  
- **RBAC:** Permissions like `vessel:read`, `vessel:write`, `port_call:read`, `da:approve`, `admin:users`. Middleware checks permission for the requested resource and tenant.  
- **Tenant isolation:** Enforced in middleware (tenant from JWT) and in every query (WHERE tenant_id = :current_tenant).

### 6.3 Application Security

- **Input validation:** All inputs validated (Pydantic); sanitize for XSS if rendered in UI.  
- **Output:** JSON responses; no sensitive data in error messages.  
- **Rate limiting:** Per-tenant and per-user limits on auth and API endpoints.  
- **CORS:** Whitelist of frontend origins only.

### 6.4 Audit & Monitoring (Security)

- **Audit log:** Every state-changing action (create/update/delete DA, user change, role change, etc.) with who, what, when, and minimal context.  
- **Immutability:** Append-only store; no updates/deletes.  
- **SIEM readiness:** Logs in structured format (e.g. JSON) and shipped to centralized logging; correlation IDs for request tracing.  
- **Anomaly detection:** Failed logins, permission denied spikes, unusual API patterns — alerts and dashboards.

---

## 7. API Design & Integration

### 7.1 API Style

- **REST** over HTTPS; **OpenAPI 3.0** specification; machine-readable schema for codegen and testing.  
- **JSON** request/response; consistent error envelope: `{ "error": { "code", "message", "details" } }`.  
- **Versioning:** URL path prefix (e.g. `/api/v1/`) or Accept header; v1 implied in this EDD.

### 7.2 Core Endpoints (Contract Summary)

| Method | Path | Purpose | Auth |
|--------|------|---------|------|
| POST | /auth/login | Email + password → access + refresh token | None |
| POST | /auth/mfa | MFA challenge | Access token (pre-MFA) or session |
| POST | /auth/refresh | Refresh token → new access token | Refresh token |
| GET  | /vessels | List vessels (tenant) | JWT, vessel:read |
| POST | /vessels | Create vessel | JWT, vessel:write |
| GET  | /vessels/{id} | Get vessel | JWT, vessel:read |
| PUT  | /vessels/{id} | Update vessel | JWT, vessel:write |
| GET  | /port-calls | List port calls (filters) | JWT, port_call:read |
| POST | /port-calls | Create port call | JWT, port_call:write |
| GET  | /port-calls/{id} | Get port call | JWT, port_call:read |
| PUT  | /port-calls/{id} | Update port call | JWT, port_call:write |
| POST | /da/generate | Generate Proforma/Final DA for port call | JWT, da:write |
| GET  | /da/{id} | Get DA | JWT, da:read |
| POST | /da/{id}/approve | Approve DA (workflow) | JWT, da:approve |
| POST | /da/{id}/send | Send DA (email + PDF) | JWT, da:send |
| POST | /ai/parse | Submit email for AI parsing (or enqueue) | JWT, ai:parse |
| GET  | /ai/parse/{job_id} | Status/result of parse job | JWT, ai:parse |
| GET  | /admin/users | List users (tenant) | JWT, admin:users |
| POST | /admin/users | Create user | JWT, admin:users |
| GET  | /admin/roles | List roles | JWT, admin:roles |

All endpoints (except login/MFA/refresh) enforce **JWT**, **tenant resolution**, and **permission check**.

### 7.3 Request/Response Examples (Conceptual)

**POST /auth/login**

- Request: `{ "email": "...", "password": "..." }`  
- Response: `{ "access_token": "...", "refresh_token": "...", "expires_in": 900, "requires_mfa": false }` or `requires_mfa: true` with next step.

**GET /port-calls?vessel_id=...&status=...**

- Response: `{ "data": [ { "id", "vessel_id", "port_id", "eta", "etd", "status", ... } ], "meta": { "total", "page", "per_page" } }`.

**POST /da/generate**

- Request: `{ "port_call_id": "...", "type": "proforma" }`.  
- Response: `{ "data": { "id", "port_call_id", "type", "status", "line_items", "totals" } }`.

### 7.4 Integration Points

- **Email:** IMAP poll or webhook (e.g. SendGrid Inbound) to ingest; store and enqueue for AI.  
- **LLM:** Internal service or 3rd party; sync or async; retries and timeouts.  
- **PDF:** Library (e.g. WeasyPrint, wkhtmltopdf, or headless Chrome) in worker; store in object storage; link in DA.  
- **Email out:** SMTP or transactional API (SendGrid, SES); templates for DA cover letter.

---

## 8. AI Processing Pipeline

### 8.1 Flow

1. **Ingest** — Email received (IMAP or webhook); persisted with `processing_status = pending`.  
2. **Enqueue** — Job pushed to Redis/queue with `email_id`, `tenant_id`.  
3. **Worker** — Picks job; loads email; calls LLM with prompt + schema.  
4. **Parse** — LLM returns structured JSON (vessel ref, port, dates, line items, amounts).  
5. **Validate** — Schema validation and business rules (e.g. currency, date range).  
6. **Persist** — Map to entities (create/update PortCall, attach parsed data to Email); set `processing_status = completed` or `failed`.  
7. **Notify** — Optional webhook or event for UI refresh.

### 8.2 Prompt & Schema

- **Prompt:** Versioned template; includes instructions, few-shot examples if needed, and output format.  
- **Output schema:** JSON schema for vessel, port, dates, line_items[] (description, amount, currency).  
- **Idempotency:** `email_id` as idempotency key; duplicate jobs do not re-write.

### 8.3 Failure Handling

- **Retries:** Configurable (e.g. 3) with backoff for transient LLM/network errors.  
- **Dead letter:** After max retries, mark email as `failed`, store error reason, alert.  
- **Manual override:** Support for operator to correct parsed data or mark as invalid.

---

## 9. DA Generator & Financial Workflow

### 9.1 Formula Engine

- **Inputs:** Port call, vessel, port, tariff (versioned), and optional AI-parsed line items.  
- **Tariff config:** Port-specific; formula or table-driven (e.g. per-call fees, per-ton fees).  
- **Output:** Line items with description, quantity, unit price, amount, currency; subtotals and totals.  
- **Versioning:** Tariff and DA version stored; history retained for audit.

### 9.2 Workflow States

- **Draft** — DA created; editable.  
- **Pending approval** — Submitted for approval (optional step).  
- **Approved** — Approved by authorized user; ready to send.  
- **Sent** — PDF generated and email dispatched; immutable.

### 9.3 PDF & Dispatch

- **PDF:** Template (e.g. HTML → PDF) with DA data and branding; stored in object storage; link in DA record.  
- **Email:** To addresses from port call or tenant config; attachment: PDF; body from template.  
- **Audit:** Approve and send actions logged with user, timestamp, and DA id.

---

## 10. DevOps, Deployment & Infrastructure

### 10.1 CI/CD

- **Pipeline:** GitHub Actions or GitLab CI.  
- **Steps:** Lint, unit tests, integration tests (e.g. Testcontainers), build Docker image, push to registry, deploy to env (dev/staging/prod).  
- **Secrets:** In CI secrets store; never in repo.  
- **Deploy:** Kubernetes apply (kubectl/Helm) or GitOps (Argo CD/Flux).

### 10.2 Deployment Topology

- **Cluster:** Kubernetes (managed or self-hosted); namespaces per environment.  
- **Backend:** Deployment, multiple replicas; HPA; readiness/liveness probes.  
- **Workers:** Separate Deployment for async jobs; scale based on queue depth.  
- **PostgreSQL:** Managed or stateful; primary + read replicas.  
- **Redis:** Managed or in-cluster; cache + queue.  
- **Ingress:** TLS termination; rate limiting; routing to backend.

### 10.3 Infrastructure as Code

- **Terraform:** Modules for network, cluster, DB, Redis, DNS, certificates.  
- **Environments:** Separate state (or workspaces) for dev, staging, prod.  
- **Changes:** Review and apply via pipeline; destructive changes require approval.

---

## 11. Observability & Resilience

### 11.1 Metrics

- **Stack:** Prometheus scrape; Grafana dashboards.  
- **Key metrics:** Request rate, latency (p50/p95/p99), error rate by endpoint and tenant; AI parse duration and success rate; DA generation duration; DB connection pool and query latency; queue depth and processing lag.

### 11.2 Logging

- **Format:** Structured (JSON); fields: timestamp, level, message, request_id, tenant_id, user_id, correlation_id.  
- **Aggregation:** ELK or equivalent; centralized search and retention.  
- **Sensitive data:** Never log passwords, tokens, or full PII; redact in log pipeline if needed.

### 11.3 Tracing

- **Distributed tracing:** Trace ID in headers and logs; span for API, DB, and external calls (LLM, email).  
- **Use:** Debug latency and dependency failures across services.

### 11.4 Resilience

- **Timeouts:** All outbound calls (DB, Redis, LLM, email) with timeouts and retries where appropriate.  
- **Circuit breaker:** Optional for external LLM/email to avoid cascade failures.  
- **Health:** `/health` (liveness), `/ready` (DB + Redis + queue connectivity) for K8s probes.

---

## 12. Threat Model & Risk Mitigation

| Threat | Mitigation |
|--------|------------|
| Unauthorized access | Strong auth (MFA), short-lived JWT, RBAC, tenant isolation |
| Data leakage | Encryption at rest and in transit; no cross-tenant access; secure secrets |
| AI manipulation / prompt injection | Input sanitization; output validation; audit of parsed data; human review for high-value DA |
| Financial fraud | Approval workflow; immutable audit log; separation of duties (create vs approve) |
| Abuse / DoS | Rate limiting; tenant quotas; monitoring and alerting |

---

## 13. Compliance & GDPR

- **Data retention:** Configurable per tenant; automated purge or archive after retention period.  
- **Right of access / portability:** Export of user and operational data (e.g. JSON/CSV) via secure download.  
- **Right to erasure:** Soft-delete or anonymize user and PII; retain audit and legal hold where required.  
- **Processing records:** Logs of processing activities; available for DPA and audits.  
- **DPA / subprocessors:** LLM and email providers treated as subprocessors; DPAs and SCCs where applicable.

---

## 14. Implementation Roadmap

| Phase | Focus | Duration (estimate) |
|-------|--------|----------------------|
| 1 | Core infrastructure: DB, auth, tenant middleware, RBAC, base API and frontend shell | 2 weeks |
| 2 | AI processing: email ingest, queue, LLM integration, parse job, persist to port call | 3 weeks |
| 3 | Financial automation: tariffs, DA formula engine, Proforma/Final DA, PDF, email dispatch, approval workflow | 3 weeks |
| 4 | Beta & security: penetration test, audit review, GDPR checks, performance tuning | 2 weeks |
| 5 | Production rollout: go-live, monitoring, runbooks, support handover | Ongoing |

---

## 15. Appendices

### Appendix A — OpenAPI Summary

- Base URL: `https://api.<env>.shipflow.ai/api/v1`  
- Auth: `Authorization: Bearer <access_token>`  
- Content-Type: `application/json`  
- Full schema to be maintained in repository (e.g. `openapi.yaml`).

### Appendix B — Environment Variables (Representative)

- `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_ACCESS_EXPIRY`, `JWT_REFRESH_EXPIRY`  
- `LLM_API_URL`, `LLM_API_KEY` (or equivalent)  
- `SMTP_*` or `SENDGRID_API_KEY` for email  
- `STORAGE_*` for PDF object storage  
- `LOG_LEVEL`, `METRICS_PORT`, `TRACE_ENDPOINT`

### Appendix C — Document History

| Version | Date | Author | Changes |
|---------|------|--------|--------|
| 1.0 | March 2026 | — | Initial EDD derived from Enterprise Technical Specification v3.0 |

---

*End of Engineering Design Document*
