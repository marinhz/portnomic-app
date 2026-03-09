# Portnomic — Agent Guidance

**Project:** Multi-tenant maritime agency SaaS — email ingestion, AI parsing, Disbursement Account (DA) generation, RBAC, audit.

**Source:** SHIPFLOW_AI_Engineering_Design_Document.md

---

## Stack Summary

| Layer | Tech |
|-------|------|
| **Frontend** | React 18+, React Router, JWT/MFA auth, tenant context, responsive UI |
| **Backend** | FastAPI, REST/OpenAPI 3.0, tenant middleware, RBAC, rate limiting |
| **Data** | PostgreSQL (tenant-scoped, `tenant_id` on all entities), Alembic migrations, Redis (cache/queue) |
| **AI** | Pluggable LLM (OpenAI-compatible), email → structured data, background workers |
| **Workers** | Celery or ARQ for AI parse, PDF generation, email dispatch |
| **Infra** | Docker, Kubernetes, Terraform, CI/CD (GitHub Actions / GitLab CI) |

---

## When to Use Which Skills

- **Backend (FastAPI, auth, services, DB)** → Use **fastapi-python** and **python-project-structure**.
- **Frontend (React, routing, UI)** → Use **react-dev**, **react-router-v7**, **tailwind-design-system**.
- **Epic 9 (Emissions)** → Use [emissions-epic.md](emissions-epic.md); it routes to Backend or Frontend per task.
- **UI tests (component, E2E, Vitest, Playwright)** → Use **ui-tests**.
- **Project layout, modules, `__all__`** → Use **python-project-structure**.

---

## Agent Roles

| Role | Brief | Use when |
|------|--------|----------|
| **Backend** | [backend.md](backend.md) | API, auth, tenant, RBAC, vessels, port calls, DA, PDF, admin, audit |
| **Frontend** | [frontend.md](frontend.md) | App shell, dashboard, vessel/port call/DA UI, auth UI, admin UI |
| **Emissions Epic** | [emissions-epic.md](emissions-epic.md) | Epic 9 — Eco-Compliance & Emissions: data model, AI parser, C-Engine, carbon price, anomaly detection, MRV export, dashboard |
| **Security** | [security.md](security.md) | Security audit, vulnerability assessment, OWASP review, remediation |
| **UI tests** | [ui-tests.md](ui-tests.md) | Component tests, E2E tests, Vitest, Playwright, React Testing Library |
| **AI pipeline** | [ai-pipeline.md](ai-pipeline.md) | Email ingest, LLM integration, parse job, structured output, idempotency |
| **DevOps** | [devops.md](devops.md) | CI/CD, K8s, Terraform, observability, secrets, health checks |

---

## Core Conventions

- **Multi-tenancy:** Every tenant-scoped query and cache key must include `tenant_id`. No cross-tenant access.
- **API:** REST, JSON, OpenAPI 3.0. Error envelope: `{ "error": { "code", "message", "details" } }`.
- **Auth:** JWT access (short-lived) + refresh; MFA (TOTP) for sensitive roles; permissions e.g. `vessel:read`, `da:approve`, `admin:users`.
- **Audit:** All state-changing actions logged (who, what, when); append-only, immutable.

Refer to the Engineering Design Document for full data model, API contracts, and NFRs.
