# Portnomic — Complete Application Functionality Reference

Single-file reference of all features, APIs, services, and UI across the Portnomic maritime agency SaaS platform.

---

## 1. Overview

**Portnomic** is a multi-tenant maritime agency SaaS with:

- AI-powered email parsing (DA, SOF, Noon Reports)
- Disbursement Account (DA) generation and approval
- Vessel and port call management
- Sentinel Operational Gap Engine (cross-source validation)
- EU ETS emission calculations and reporting
- OAuth/IMAP email integration
- Stripe/MyPOS billing
- RBAC, MFA, and GDPR tools

---

## 2. Tech Stack

| Layer        | Stack                                                  |
|-------------|---------------------------------------------------------|
| Backend     | Python 3.11+, FastAPI, SQLAlchemy 2.0 (async), PostgreSQL, Redis, Alembic |
| Frontend    | React 18, TypeScript, Vite, Tailwind CSS v4, React Router v7, Axios |
| Infra       | Docker Compose (PostgreSQL 16, Redis 7)               |
| AI/LLM      | OpenAI-compatible API (BYOAI per tenant)               |
| Billing     | Stripe (checkout), MyPOS (webhook)                     |

---

## 3. API Endpoints (Backend)

Base URL: `/api/v1` where applicable.

### 3.1 Auth — `/api/v1/auth`

| Method | Path                | Description                    | Auth |
|--------|---------------------|--------------------------------|------|
| POST   | /login              | Login with email/password      | None |
| POST   | /mfa                | MFA verification               | MFA token |
| POST   | /refresh            | Refresh access token           | Refresh token |
| GET    | /me                 | Current user info              | JWT |
| POST   | /change-password    | Change password                | JWT |
| GET    | /mfa/setup          | MFA setup QR code/secret       | JWT |
| POST   | /mfa/confirm        | Confirm MFA enrollment         | JWT |
| POST   | /mfa/disable        | Disable MFA                    | JWT |

### 3.2 Vessels — `/api/v1/vessels`

| Method | Path       | Description       | Auth |
|--------|------------|-------------------|------|
| GET    | /          | List vessels      | JWT + vessel:read |
| POST   | /          | Create vessel     | JWT + vessel:write |
| GET    | /{id}      | Get vessel        | JWT + vessel:read |
| PUT    | /{id}      | Update vessel     | JWT + vessel:write |

### 3.3 Ports — `/api/v1/ports`

| Method | Path       | Description       | Auth |
|--------|------------|-------------------|------|
| GET    | /          | List ports        | JWT + port_call:read |
| POST   | /          | Create port       | JWT + port_call:write |
| GET    | /{id}      | Get port          | JWT + port_call:read |
| PUT    | /{id}      | Update port       | JWT + port_call:write |

### 3.4 Port Calls — `/api/v1/port-calls`

| Method | Path                                      | Description                          | Auth |
|--------|--------------------------------------------|--------------------------------------|------|
| GET    | /                                          | List port calls                      | JWT + port_call:read |
| POST   | /                                          | Create port call                     | JWT + port_call:write |
| GET    | /{id}                                      | Get port call                        | JWT + port_call:read |
| PUT    | /{id}                                      | Update port call                     | JWT + port_call:write |
| POST   | /{id}/audit                                | Trigger Sentinel audit               | JWT + port_call:read |
| GET    | /{id}/discrepancies                        | List discrepancies                   | JWT + port_call:read |
| DELETE | /{id}/discrepancies                        | Clear discrepancies                   | JWT + port_call:write |
| POST   | /{id}/upload                               | Upload document (multipart)          | JWT + port_call:write |
| POST   | /{id}/documents                            | Create document (base64)             | JWT + port_call:write |
| GET    | /{id}/documents                            | List documents                       | JWT + port_call:read |
| GET    | /{id}/documents/parse-status/{job_id}     | Get document parse job status        | JWT + port_call:read |

### 3.5 Tariffs — `/api/v1/tariffs`

| Method | Path       | Description       | Auth |
|--------|------------|-------------------|------|
| GET    | /          | List tariffs      | JWT |
| POST   | /          | Create tariff     | JWT |
| GET    | /{id}      | Get tariff        | JWT |
| PUT    | /{id}      | Update tariff     | JWT |

### 3.6 Disbursement Accounts (DA) — `/api/v1/da`

| Method | Path         | Description            | Auth |
|--------|--------------|------------------------|------|
| GET    | /            | List DAs               | JWT |
| POST   | /generate    | Generate DA from params | JWT |
| GET    | /{id}        | Get DA                 | JWT |
| GET    | /{id}/anomalies | List DA anomalies   | JWT |
| GET    | /{id}/pdf    | Download DA PDF        | JWT |
| POST   | /{id}/approve| Approve DA             | JWT |
| POST   | /{id}/send   | Send DA by email       | JWT |

### 3.7 Emails — `/api/v1/emails`

| Method | Path       | Description         | Auth |
|--------|------------|---------------------|------|
| GET    | /          | List emails         | JWT + ai:parse |
| GET    | /{id}      | Get email detail    | JWT + ai:parse |
| PATCH  | /{id}      | Update email status | JWT + ai:parse |
| DELETE | /{id}      | Delete email        | JWT + ai:parse |

### 3.8 AI Parsing — `/api/v1/ai`

| Method | Path               | Description              | Auth |
|--------|--------------------|--------------------------|------|
| POST   | /parse             | Submit email for parsing | JWT + ai:parse |
| GET    | /parse/{job_id}    | Get parse job status     | JWT + ai:parse |
| PUT    | /emails/{id}/status| Manual override status   | JWT + ai:parse |

### 3.9 Emissions — `/api/v1/emissions`

| Method | Path                | Description                  | Auth |
|--------|---------------------|------------------------------|------|
| GET    | /summary            | Emission summary             | JWT |
| GET    | /reports            | List emission reports        | JWT |
| POST   | /parse              | Parse emission document      | JWT |
| GET    | /parse/{job_id}     | Parse job status             | JWT |
| GET    | /reports/{id}       | Get report detail            | JWT |
| PATCH  | /reports/{id}       | Update report                | JWT |
| GET    | /reports/{id}/export| Export report (CSV)          | JWT |
| POST   | /calculate          | Calculate emissions          | JWT |

### 3.10 Admin — `/api/v1/admin`

| Method | Path           | Description            | Auth |
|--------|----------------|------------------------|------|
| GET    | /users         | List users             | JWT + admin:users |
| POST   | /users         | Create user            | JWT + admin:users |
| GET    | /users/{id}    | Get user               | JWT + admin:users |
| PUT    | /users/{id}    | Update user            | JWT + admin:users |
| GET    | /permissions   | Permissions manifest   | JWT + admin:users |
| GET    | /roles         | List roles             | JWT + admin:roles |
| GET    | /roles/{id}    | Get role               | JWT + admin:roles |
| POST   | /roles         | Create role            | JWT + admin:roles |
| PUT    | /roles/{id}    | Update role            | JWT + admin:roles |

### 3.11 Platform (super-admin) — `/api/v1/platform`

| Method | Path              | Description   | Auth |
|--------|-------------------|---------------|------|
| POST   | /tenants          | Create tenant | JWT + platform admin |
| GET    | /tenants          | List tenants  | JWT + platform admin |
| GET    | /tenants/{id}     | Get tenant    | JWT + platform admin |
| PATCH  | /tenants/{id}     | Update tenant | JWT + platform admin |

### 3.12 Integrations — `/api/v1/integrations/email`

| Method | Path         | Description              | Auth |
|--------|--------------|--------------------------|------|
| GET    | /connect     | Start OAuth flow         | JWT + admin:users |
| GET    | /callback    | OAuth callback           | State token |
| GET    | /            | List mail connections    | JWT + admin:users |
| POST   | /sync        | Trigger sync now         | JWT + admin:users |
| DELETE | /{id}        | Disconnect mailbox       | JWT + admin:users |
| POST   | /imap/test   | Test IMAP connection     | JWT + admin:users |
| POST   | /imap        | Add IMAP connection      | JWT + admin:users |

### 3.13 AI Settings — `/api/v1/settings`

| Method | Path                        | Description           | Auth |
|--------|-----------------------------|-----------------------|------|
| GET    | /ai                         | Get AI config         | JWT + admin:users |
| PUT    | /ai                         | Update AI config     | JWT + admin:users |
| DELETE | /ai                         | Delete AI config     | JWT + admin:users |
| GET    | /ai/prompts                 | List prompt overrides | JWT + admin:users |
| PUT    | /ai/prompts/{parser_type}   | Set prompt override   | JWT + admin:users |
| POST   | /ai/prompts/{parser_type}/reset | Reset prompt     | JWT + admin:users |
| POST   | /ai/test                    | Test LLM connection  | JWT + admin:users |

### 3.14 GDPR — `/api/v1/gdpr`

| Method | Path               | Description             | Auth |
|--------|--------------------|-------------------------|------|
| POST   | /export            | Export own data         | JWT |
| POST   | /export/{user_id}  | Export user data (admin)| JWT + admin:users |
| POST   | /erasure           | Erasure request         | JWT |
| GET    | /retention         | Retention policy        | JWT |
| PUT    | /retention         | Update retention        | JWT |
| GET    | /processing-records| Processing records      | JWT |

### 3.15 Billing — `/api/v1/billing`

| Method | Path              | Description            | Auth |
|--------|-------------------|------------------------|------|
| GET    | /status           | Billing status         | JWT |
| POST   | /create-checkout-session | Stripe checkout  | JWT |
| POST   | /portal           | Stripe portal          | JWT |
| POST   | /cancel-return     | Cancel return handler  | JWT |
| POST   | /webhooks/mypos   | MyPOS webhook          | Webhook |

### 3.16 Webhooks — `/webhooks`

| Method | Path           | Description       | Auth |
|--------|----------------|-------------------|------|
| POST   | /inbound-email | Inbound email     | Signature |

### 3.17 Health & Metrics

| Method | Path     | Description           | Auth |
|--------|----------|-----------------------|------|
| GET    | /health  | Liveness probe        | None |
| GET    | /ready   | Readiness (DB+Redis)  | None |
| GET    | /metrics | Prometheus metrics    | None |

---

## 4. Backend Services (Business Logic)

| Service               | Purpose                                                         |
|-----------------------|-----------------------------------------------------------------|
| `admin`               | User/role CRUD, permissions manifest                            |
| `audit`               | Append-only audit logging (correlation ID, tenant, user)        |
| `audit_service`       | Audit orchestration for Sentinel                                |
| `cache`               | Redis caching with TTL and pattern delete                       |
| `carbon_price`        | EU carbon price from external API                              |
| `disbursement_account`| DA generation, line items, approval, invoice number             |
| `discrepancy`         | Resolve source labels, list/delete discrepancies                 |
| `document_extraction`  | PDF/XLSX/JPG text extraction                                   |
| `document_service`    | Document CRUD, content hash deduplication                       |
| `email_dispatch`      | Send DA emails                                                  |
| `email_service`       | Email CRUD, status updates                                      |
| `emission_anomaly`    | Emission anomaly detection                                      |
| `emission_calculator` | CO2, EU ETS calculations, EUA estimates                        |
| `emission_export`     | CSV export of emission reports                                  |
| `emission_parser`     | Parse/normalize emission data                                   |
| `formula_engine`      | Tariff formula evaluation                                       |
| `gdpr`                | Data export, erasure, retention policy, processing records      |
| `leakage_audit_trigger`| Trigger leakage audit after financial doc parse               |
| `llm_client`          | OpenAI-compatible LLM calls (BYOAI), parse, test                |
| `mail_connection`     | OAuth and IMAP connection management                            |
| `oauth_ingest`        | Poll Gmail, Outlook, IMAP for emails                            |
| `parse_job_service`   | Parse job state and queueing                                    |
| `parse_worker`        | Process emails/documents, create port calls, emission reports, DAs |
| `pdf_generator`       | DA PDF and HTML rendering                                       |
| `port`                | Port CRUD                                                       |
| `port_call`           | Port call CRUD                                                  |
| `prompt_override_svc` | Per-parser prompt overrides                                     |
| `sentinel/AuditEngine`| Triple-Check rules (tug/pilot, berthage, fuel)                 |
| `sentinel/ais_client` | AIS berth data from aisstream.io                                |
| `sentinel/ais_normalizer` | Normalize AIS to TimelineEvent                              |
| `sentinel/da_normalizer`  | Normalize DA to TimelineEvent                                |
| `sentinel/noon_report_normalizer` | Normalize Noon Report to TimelineEvent                   |
| `sentinel/sof_normalizer`    | Normalize SOF to TimelineEvent                            |
| `sentinel/timeline_aggregator` | Aggregate events from all sources                          |
| `sentinel/time_overlap`     | Interval overlap logic                                      |
| `sentinel_audit_trigger`    | Trigger Sentinel audit after parse (DA/SOF/Noon)              |
| `storage`             | Blob storage (local/S3)                                         |
| `tariff`              | Tariff CRUD, active tariff selection                            |
| `tenant`              | Tenant CRUD                                                     |
| `tenant_llm_config_svc`| Per-tenant LLM config                                           |
| `vessel`              | Vessel CRUD                                                     |
| `vessel_filter`       | Vessel-related email heuristics                                 |
| `report_type_detector`| Detect emission report type                                     |
| `limits`              | Plan limits (Starter/Professional/Enterprise)                   |

---

## 5. Backend Models (Database)

| Model               | Purpose                                          |
|---------------------|--------------------------------------------------|
| `Base`, `TimestampMixin`, `TenantMixin` | Shared base and mixins |
| `Anomaly`           | Emission anomalies, leakage anomalies            |
| `AuditLog`          | Immutable audit entries                          |
| `DisbursementAccount`| DA with line items, status, invoice number      |
| `Discrepancy`       | Sentinel discrepancies (severity, loss, rule_id)  |
| `Document`          | Manual uploads, content hash, parse status       |
| `Email`             | Ingested emails, parse status                     |
| `EmissionReport`    | Emission data, fuel entries                       |
| `FuelEntry`         | Fuel consumption per report                       |
| `MailConnection`    | OAuth/IMAP connections                            |
| `ParseJob`          | AI parse job queue                               |
| `Port`              | Port directory                                   |
| `PortCall`          | Port call with vessel, port, ETA/ETD             |
| `Role`              | RBAC roles                                       |
| `Tenant`            | Multi-tenant org, subscription                   |
| `TenantLlmConfig`   | Per-tenant LLM provider/key                      |
| `TenantPromptOverride`| Per-parser prompt overrides                    |
| `User`              | Users, MFA, tenant association                   |
| `Vessel`            | Vessel registry                                  |
| `Tariff`            | Tariff configurations                            |

---

## 6. Background Worker (ARQ)

| Task                 | Trigger               | Purpose                                          |
|----------------------|-----------------------|--------------------------------------------------|
| `process_parse_job`  | Redis queue           | AI parse email → port call, emission report, DA  |
| `imap_poll_task`     | Periodic              | Poll IMAP mailboxes for new emails               |
| `poll_queue`         | Periodic              | Poll OAuth (Gmail/Outlook) for new emails         |
| `da_worker`          | DA generation         | Generate DA PDF, persist, trigger audit         |

Parse worker flow: email/document → LLM parse → resolve vessel/port → create/update port call → create emission report / DA → trigger Sentinel / leakage audit when relevant.

---

## 7. Sentinel Operational Gap Engine

**Data sources:**
- **A (Financial):** Disbursement Accounts (DA line items)
- **B (Operational):** Statement of Facts (SOF) — tug fast/off, pilot on/off
- **C (Vessel):** Noon Reports — fuel, GPS, engine hours
- **D (External):** AIS (aisstream.io) — berth arrival/departure

**Triple-Check rules:**
1. Temporal Tug/Pilot Audit: DA invoiced hours vs SOF timestamps + buffer
2. Berthage verification: DA berth days vs AIS berth stay
3. Fuel paradox: High consumption while idle (SOF anchorage)

**Output:** Discrepancies stored with severity, estimated loss, rule_id, raw_evidence.

**Triggers:** After DA/SOF/Noon parse; idempotent; gated by plan (Professional/Enterprise).

---

## 8. Frontend Routes & Pages

| Path                       | Component             | Description                        |
|----------------------------|-----------------------|------------------------------------|
| /                          | Dashboard             | Main dashboard                     |
| /login                     | LoginPage             | Login, MFA                         |
| /vessels                   | VesselList            | Vessel list                        |
| /vessels/new               | VesselForm            | Create vessel                      |
| /vessels/:id               | VesselDetail          | Vessel detail                      |
| /vessels/:id/edit          | VesselForm            | Edit vessel                        |
| /port-calls                | PortCallList          | Port call list                     |
| /port-calls/new            | PortCallWizard        | Create port call wizard            |
| /port-calls/:id            | PortCallDetail        | Port call detail                   |
| /port-calls/:id/audit      | PortCallAudit         | Sentinel side-by-side audit        |
| /port-calls/:id/documents  | PortCallDocuments     | Document uploads, parse status     |
| /port-calls/:id/edit       | PortCallForm          | Edit port call                     |
| /da                        | DAList                | DA list                            |
| /da/generate               | DAGenerate            | Generate DA                        |
| /da/:id                    | DADetail              | DA detail, approve, send           |
| /emails                    | EmailList             | Email inbox                        |
| /emails/:id                | EmailDetail           | Email detail, parse                |
| /emissions                 | EmissionsDashboard    | Emission summary and reports       |
| /emissions/reports/:id     | EmissionsReportDetail | Emission report detail             |
| /leakage-detector          | LeakageDetectorPage   | Leakage anomaly view               |
| /directory/ports          | PortDirectory         | Port directory                     |
| /directory/tariffs         | TariffConfig          | Tariff configuration               |
| /settings/profile          | ProfilePage           | User profile                       |
| /settings/integrations    | IntegrationsPage      | OAuth/IMAP connections             |
| /settings/billing         | Billing               | Billing status, upgrade             |
| /settings/ai              | AISettingsPage        | AI/LLM config, prompts             |
| /admin/users              | UserList              | User management                    |
| /admin/users/new          | UserForm              | Create user                        |
| /admin/users/:id/edit     | UserForm              | Edit user                          |
| /admin/roles              | RoleList              | Role management                    |
| /admin/roles/new          | RoleForm              | Create role                        |
| /admin/roles/:id/edit     | RoleForm              | Edit role                          |
| /admin/companies          | CompanyList/Detail/Form| Platform tenant management        |

---

## 9. Frontend Components

| Component             | Purpose                                       |
|-----------------------|-----------------------------------------------|
| AppLayout             | App shell, sidebar navigation                 |
| Sidebar               | Main navigation                               |
| AuthContext           | Auth state, login, refresh                    |
| ProtectedRoute        | JWT-protected routes                          |
| PlatformAdminRoute     | Platform admin only                           |
| AdminAISettingsRoute   | Admin + AI settings permission                 |
| DataTable              | Paginated data table                          |
| Pagination             | Pagination controls                           |
| SearchableSelect       | Searchable dropdown                            |
| FileUploader           | File upload UI                                |
| TariffFormModal        | Tariff create/edit modal                      |
| LinkToPortCallModal    | Link email/doc to port call                   |
| PlanUpgradeGate        | Feature-gating for plan limits                |
| SentinelAlert          | Sentinel discrepancy alert card              |
| SideBySideAudit        | Vendor claims vs operational reality table    |
| LoadingSpinner         | Loading indicator                             |
| ErrorPage, NotFoundPage| Error handling                                |
| shadcn/ui              | Button, Card, Dialog, Input, Badge, etc.      |

---

## 10. Feature Domains Summary

| Domain          | Features                                                                 |
|-----------------|---------------------------------------------------------------------------|
| Auth            | Login, MFA (TOTP), refresh, password change, RBAC                          |
| Vessels         | CRUD, IMO/MMSI, type, flag                                                |
| Ports           | CRUD, coordinates, directory                                               |
| Port Calls      | CRUD, ETA/ETD, agent, documents, Sentinel audit, discrepancies           |
| Documents       | Manual upload, parse, content hash, SOF/DA/Noon categories               |
| Emails          | Inbox, OAuth/IMAP ingest, parse, link to port call                       |
| AI Parsing      | DA/SOF/Noon/emission extraction, BYOAI, prompt overrides                  |
| Disbursement    | DA generation, line items, approval, PDF, email dispatch                  |
| Emissions       | Emission reports, EU ETS, fuel types, export CSV                          |
| Sentinel        | Triple-Check audit, AIS berth data, discrepancies, source labels         |
| Leakage         | Financial document audit, anomaly detection                               |
| Tariffs         | Formula-based tariff config                                               |
| Admin           | Users, roles, permissions, companies (platform)                          |
| Integrations    | Gmail, Outlook OAuth, IMAP                                                 |
| Billing         | Stripe checkout, MyPOS webhook, plan status                               |
| GDPR            | Export, erasure, retention policy, processing records                    |

---

## 11. Security & Infrastructure

- JWT access (15 min) + refresh (7 days)
- MFA (TOTP) with encrypted secrets
- RBAC with tenant-scoped permissions
- Strict multi-tenant isolation
- Append-only audit logging
- Rate limiting per IP
- CORS restricted to frontend origin
- Security headers middleware
- Prometheus metrics
- OpenTelemetry tracing

---

*Generated: Application functionality reference for Portnomic.*
