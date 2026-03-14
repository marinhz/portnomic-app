# ShipFlow AI — Project Overview

**Source:** [SHIPFLOW_AI_Engineering_Design_Document.md](../SHIPFLOW_AI_Engineering_Design_Document.md)  
**Last updated:** March 2026

This document summarizes what has been **implemented**, **improved**, and **added** relative to the original Engineering Design Document (EDD).

---

## Table of Contents

1. [What Is Done (EDD Implementation)](#1-what-is-done-edd-implementation)
2. [What Is Improved](#2-what-is-improved)
3. [What Is Added (Beyond EDD)](#3-what-is-added-beyond-edd)
4. [EDD Section Mapping](#4-edd-section-mapping)

---

## 1. What Is Done (EDD Implementation)

### 1.1 Core Infrastructure (EDD Phase 1)

| EDD Component | Status | Implementation |
|---------------|--------|----------------|
| **Database schema & migrations** | ✅ Done | PostgreSQL + Alembic; Tenant, User, Role, Vessel, Port, PortCall, Email, Tariff, DA, AuditLog |
| **Redis** | ✅ Done | Session, idempotency keys, parse job queue |
| **API gateway** | ✅ Done | FastAPI, CORS, rate limiting, request ID, error envelope |
| **Auth service** | ✅ Done | Login, JWT (access + refresh), MFA (TOTP) |
| **Tenant middleware** | ✅ Done | Resolve tenant from JWT; inject into request context |
| **RBAC middleware** | ✅ Done | Permission checks (`vessel:read`, `da:approve`, `admin:users`, etc.) |
| **Vessel service** | ✅ Done | CRUD vessels (tenant-scoped) |
| **Port call service** | ✅ Done | CRUD port calls, link to vessel |
| **Admin service** | ✅ Done | User/role CRUD (tenant-scoped) |
| **Audit logger** | ✅ Done | Append-only audit events |
| **Frontend app shell** | ✅ Done | React 18, routing, auth state, tenant context |
| **Auth UI** | ✅ Done | Login, MFA challenge, password reset |
| **API client** | ✅ Done | Axios, JWT attach, refresh, error handling |
| **Dashboard** | ✅ Done | Vessels, port calls, DA list, KPIs |
| **Admin UI** | ✅ Done | User/role management (RBAC-driven) |

### 1.2 AI Processing (EDD Phase 2)

| EDD Component | Status | Implementation |
|---------------|--------|----------------|
| **Email entity** | ✅ Done | Persistence with `processing_status`, `ai_raw_output` |
| **Email ingest** | ✅ Done | IMAP poll (worker) + webhook (SendGrid-style) |
| **Parse job queue** | ✅ Done | Redis list `shipflow:parse_jobs` |
| **Background worker** | ✅ Done | ARQ (async Redis queue) |
| **Idempotency** | ✅ Done | Same `email_id` not processed twice |
| **LLM client** | ✅ Done | OpenAI-compatible API (gpt-4o-mini default) |
| **Prompt & schema** | ✅ Done | Versioned prompts, JSON output schema |
| **Parse worker** | ✅ Done | Validate, persist, link to port call/vessel |
| **Retries & failure** | ✅ Done | Configurable retries, backoff, dead letter |
| **AI parse API** | ✅ Done | `POST /ai/parse`, `GET /ai/parse/{job_id}` |
| **Frontend parse UI** | ✅ Done | Trigger parse, show job status/result |

### 1.3 Financial Automation (EDD Phase 3)

| EDD Component | Status | Implementation |
|---------------|--------|----------------|
| **Tariff entity** | ✅ Done | Port-specific, versioned, formula config |
| **DA entity** | ✅ Done | Proforma/Final, workflow states (draft → pending_approval → approved → sent) |
| **DA formula engine** | ✅ Done | Port call, vessel, tariff, AI-parsed line items → line items |
| **DA generate API** | ✅ Done | `POST /da/generate`, `GET /da/{id}` |
| **DA approve API** | ✅ Done | `POST /da/{id}/approve` |
| **PDF generation** | ✅ Done | Worker, template, stored in S3 |
| **Email dispatch** | ✅ Done | Worker, SMTP, DA cover letter |
| **DA send API** | ✅ Done | `POST /da/{id}/send` |
| **DA workspace frontend** | ✅ Done | Proforma/Final view, approve, PDF, send |

### 1.4 Beta & Security (EDD Phase 4)

| EDD Component | Status | Implementation |
|---------------|--------|----------------|
| **Penetration test** | ✅ Done | Scope defined, remediation tracked |
| **Threat mitigation** | ✅ Done | Verification tasks |
| **Application security** | ✅ Done | Review, input validation, security headers |
| **Audit log coverage** | ✅ Done | State-changing actions logged |
| **GDPR** | ✅ Done | Data export, right to erasure, processing records |
| **Health/readiness** | ✅ Done | `/health`, `/ready` (DB, Redis, queue) |
| **Structured logging** | ✅ Done | JSON, request_id, tenant_id, correlation_id |

### 1.5 Production Rollout (EDD Phase 5)

| EDD Component | Status | Implementation |
|---------------|--------|----------------|
| **CI/CD** | ✅ Done | GitHub Actions, Docker build, deploy |
| **Kubernetes** | ✅ Done | Deployments for backend, worker, frontend |
| **Prometheus & Grafana** | ✅ Done | Metrics, dashboards |
| **Alerting** | ✅ Done | Alertmanager, Slack/PagerDuty |
| **Distributed tracing** | ✅ Done | OpenTelemetry, OTLP |
| **Resilience** | ✅ Done | Circuit breaker (LLM), timeouts, retries |
| **HPA** | ✅ Done | Backend and worker scaling |
| **Runbooks** | ✅ Done | Incidents, auth failures, queue backlog, etc. |
| **All-in-one container** | ✅ Done | Easy deploy & develop (API + worker + frontend) |

---

## 2. What Is Improved

Improvements beyond the original EDD specification:

| Area | Improvement |
|------|-------------|
| **Platform branding** | Rebranded from ShipFlow to **Portnomic** (Oxford Blue + Success Green) |
| **UI/UX** | shadcn/ui components, Lucide icons, Sonner toasts, consistent design system |
| **Resilience** | Circuit breaker on LLM client (5 failures → open, 30s recovery); exponential backoff |
| **Observability** | Prometheus middleware, custom metrics (HTTP, auth, AI, DB, queue); Loki for logs |
| **Security headers** | HSTS, X-Content-Type-Options, X-Frame-Options, CSP-ready |
| **Request context** | Request ID, correlation ID in logs and responses |
| **Multi-tenancy** | Companies entity for strict tenant isolation; platform admin for tenant management |
| **Role management** | Full CRUD for roles (create, edit); permissions manifest API for dynamic UI |
| **User profile** | User profile system (preferences, avatar) |
| **Session persistence** | Auth state survives page refresh (token storage strategy) |
| **AI integration test** | Connection test endpoint with improved error handling |
| **Parse flow bugs** | Fixes for redirect 404, newly synced email no-op, status reset |

---

## 3. What Is Added (Beyond EDD)

Epics and features not in the original EDD roadmap:

### Epic 6 — Email Connection (OAuth 2.0 & UI)

| Feature | Description |
|---------|-------------|
| **OAuth 2.0** | Gmail and Microsoft 365/Outlook mailbox connection via OAuth |
| **Per-tenant mailboxes** | Each tenant connects their own mailbox; no single global IMAP only |
| **IMAP connection** | Optional IMAP connection per tenant (host, user, encrypted password) |
| **Settings / Integrations UI** | `/settings/integrations` — Connect Gmail, Connect Outlook, Add IMAP, Disconnect |
| **Token storage** | Encrypted access/refresh tokens; auto-refresh; error status on failure |
| **Ingest from OAuth** | Worker fetches from Gmail API / Microsoft Graph; backward compatible with global IMAP |

### Epic 7 — UX & UI Polish

| Feature | Description |
|---------|-------------|
| **shadcn/ui** | Button, Card, Input, Dialog, DropdownMenu, and other primitives |
| **Lucide React** | Icons for navigation, actions, status indicators |
| **Sonner** | Global toast system (success, error, info) |
| **Visual polish** | Consistent spacing, typography, loading states, empty states |
| **Theme switcher** | Light/dark mode support |
| **Menu redesign** | Improved navigation and analysis menu structure |

### Epic 8 — Business & Monetization

| Feature | Description |
|---------|-------------|
| **Monetization plan** | Tiered plans: Demo, Starter, Professional, Enterprise |
| **Subscription data model** | Tenant plan, status (active/trial/canceled), limits |
| **Billing integration** | Stripe (legacy) → **myPOS** migration for payment processing |
| **Feature gating** | Limits on users, vessels, DAs/month, AI parses; enforced in backend |
| **Billing admin UI** | Subscription status, upgrade/downgrade, usage display |
| **Plan upgrade gates** | Upgrade CTA when limits reached or premium features accessed |

### Epic 9 — Eco-Compliance & Emissions Reporting

| Feature | Description |
|---------|-------------|
| **Emission data model** | Emission reports linked to emails and port calls |
| **Noon / bunker report parser** | AI extraction of fuel consumption from emails |
| **C-Engine** | CO₂ formula (E = C × f); EU ETS cost projection |
| **Carbon price API** | Current carbon market price for EUA estimates |
| **Anomaly detection** | AI Auditor flags impossible consumption, fuel-type mismatches |
| **EU MRV export** | JSON/XML/PDF for Monitoring, Reporting, Verification |
| **Emissions dashboard** | Carbon debt, compliance status (Green/Yellow/Red), activity logs |

### Epic 10 — Bring Your Own AI (BYOAI)

| Feature | Description |
|---------|-------------|
| **Tenant LLM config** | Per-tenant API key, base URL, model (OpenAI-compatible) |
| **Encrypted storage** | API keys encrypted at rest; never logged or exposed |
| **Tenant-aware routing** | Parse worker uses tenant config when available; fallback to platform default |
| **Prompt overrides** | Custom prompts for DA parsing and emission parsing per tenant |
| **Admin AI settings UI** | Settings → AI Integration (keys), AI Prompts (edit/reset) |
| **Premium gating** | BYOAI only for Professional and Enterprise plans |

### Epic 11 — Roles & Permissions Redesign

| Feature | Description |
|---------|-------------|
| **Permissions manifest API** | `GET /api/v1/admin/permissions` — Grouped permissions with labels |
| **Module-based grouping** | Vessels, Port calls, DA, AI, Admin, Billing, Settings |
| **User-friendly labels** | "View disbursements" instead of `da:read` |
| **Role presets** | Templates (e.g. Operations Manager, Finance Only) for quick setup |
| **Role list summary** | Permission summary by module for scannability |

---

## 4. EDD Section Mapping

| EDD § | Section | Status |
|-------|---------|--------|
| 1 | Document Purpose & Scope | Reference |
| 2 | System Context & Requirements | FR-1 to FR-9, NFR-1 to NFR-6 implemented |
| 3 | Architecture Overview | Layered architecture, multi-tenancy implemented |
| 4 | Component Design | Presentation, Application, Data, AI, Infrastructure layers done |
| 5 | Data Model & Persistence | Core entities + Email, Tariff, DA, AuditLog; indexes; retention policy |
| 6 | Security Design | Encryption, JWT/MFA, RBAC, tenant isolation, audit, rate limiting |
| 7 | API Design & Integration | REST, OpenAPI, core endpoints; error envelope |
| 8 | AI Processing Pipeline | Ingest, queue, worker, LLM, validate, persist, notify |
| 9 | DA Generator & Financial Workflow | Formula engine, workflow states, PDF, dispatch |
| 10 | DevOps, Deployment & Infrastructure | CI/CD, K8s, Terraform, IaC |
| 11 | Observability & Resilience | Metrics, logging, tracing, health, circuit breaker |
| 12 | Threat Model & Risk Mitigation | Addressed via pen test, security review |
| 13 | Compliance & GDPR | Export, erasure, processing records |
| 14 | Implementation Roadmap | Phases 1–5 largely complete; extended with Epics 6–11 |

---

## Summary

- **EDD Phases 1–3** (Core, AI, Financial): Fully implemented.
- **EDD Phases 4–5** (Beta, Production): Implemented with runbooks, observability, and deployment tooling.
- **Improvements**: Portnomic rebrand, shadcn/Lucide/Sonner, resilience, observability, security hardening.
- **Additions**: OAuth email (Epic 6), UX polish (Epic 7), monetization (Epic 8), emissions (Epic 9), BYOAI (Epic 10), roles redesign (Epic 11).

---

*End of Project Overview*
