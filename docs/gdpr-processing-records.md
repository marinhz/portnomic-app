# GDPR Article 30 — Records of Processing Activities

**Document Type:** Compliance — Processing Records  
**Source:** ShipFlow AI Engineering Design Document (EDD) §13  
**Version:** 1.0  
**Date:** March 2026  
**Classification:** Internal — Compliance

---

## 1. Data Controller Information

| Field | Value |
|-------|-------|
| **Name** | *[Customer / Data Controller — to be completed]* |
| **Address** | *[Address — to be completed]* |
| **Contact (DPO)** | *[DPO email — to be completed]* |
| **Representative (if outside EU)** | *[If applicable]* |

*Note: ShipFlow is operated as a SaaS platform. The customer (maritime agency) is typically the data controller for their operational data. The platform operator may act as data processor under a Data Processing Agreement (DPA).*

---

## 2. Processing Activities

| Activity | Data Categories | Purpose | Legal Basis | Retention | Safeguards | Recipients |
|----------|-----------------|---------|-------------|-----------|------------|------------|
| **User registration & authentication** | Email, password hash, MFA secret (encrypted), name, role | Account creation, login, MFA verification | Contract performance; Legitimate interest (security) | Account lifetime + 30 days post-deletion | Password hashing (bcrypt), MFA secret encryption, JWT short-lived tokens | None (internal only) |
| **Port call management** | Vessel refs, port refs, ETA/ETD, status, vessel/port metadata | Operational management of vessel visits | Contract performance | Per tenant policy (e.g. 7 years for financial records) | RBAC, tenant isolation, audit logging | None (internal only) |
| **Email ingestion & AI parsing** | Email headers, body (text/HTML), attachments metadata, parsed structured data (vessel, port, dates, amounts) | Extract maritime data from operational emails | Contract performance; Legitimate interest (automation) | Per tenant policy; align with dispute resolution needs | Input sanitization, output validation, human review for high-value DA, tenant isolation | OpenAI (subprocessor — LLM) |
| **Disbursement account generation** | Port call data, tariff configs, line items, amounts, currency, PDF output | Generate and dispatch DA to shipowners | Contract performance | 7 years (financial records) | Approval workflow, immutable audit, separation of duties | SMTP provider (subprocessor — email dispatch) |
| **Audit logging** | User ID, action, resource type/ID, IP, user agent, minimal payload | Security, compliance, incident investigation | Legal obligation; Legitimate interest | 7 years (compliance); immutable | Append-only store, no updates/deletes, SIEM-ready | Internal; SIEM/log aggregation (if configured) |
| **Analytics & metrics** | Aggregated usage, latency, error rates, tenant-level KPIs (non-PII) | Service improvement, capacity planning | Legitimate interest | 24 months | Anonymized/aggregated; no PII in metrics | Internal; monitoring provider (if applicable) |

---

## 3. Subprocessors

| Subprocessor | Purpose | Data Processed | Location | DPA / SCC |
|--------------|---------|----------------|----------|-----------|
| **OpenAI** | LLM for email parsing (structured extraction) | Email content (headers, body) sent for parsing | US (API) | DPA; SCCs where required |
| **SMTP provider** (e.g. SendGrid, SES) | Outbound email dispatch (DA cover letter + PDF) | Recipient email, DA content, PDF attachment | Per provider | DPA; SCCs where required |
| **Cloud hosting provider** (e.g. AWS, GCP, Azure) | Compute, database, object storage, networking | All platform data (encrypted at rest) | Per deployment region | DPA; SCCs where required |

*Subprocessor list must be maintained and updated; customers should be notified of changes per DPA.*

---

## 4. Data Flows

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           SHIPFLOW DATA FLOW                                      │
└─────────────────────────────────────────────────────────────────────────────────┘

  INGEST                    PARSE                      DA                      STORAGE
  ──────                    ─────                      ──                      ───────
  Email (IMAP/Webhook)  →   AI Parse (OpenAI)    →   DA Generator    →   PostgreSQL
       │                           │                        │                    │
       │                           │                        │                    │
       ▼                           ▼                        ▼                    ▼
  Raw email stored           Structured data         Proforma/Final         Encrypted
  (tenant-scoped)            linked to port call     PDF + email           at rest
                                                      dispatch

  EXPORT
  ──────
  Data subject access / portability: JSON/CSV export via secure download
  Erasure: Soft-delete or anonymize per retention policy; audit retained where required
```

---

## 5. Data Subject Rights

| Right | Implementation | Notes |
|-------|----------------|-------|
| **Access (Art. 15)** | Export of user and operational data (JSON/CSV) via secure download | API or admin UI; tenant-scoped |
| **Portability (Art. 20)** | Machine-readable export (JSON) of data provided by data subject | Align with access export |
| **Erasure (Art. 17)** | Soft-delete or anonymize user and PII; retain audit/legal hold where required | Per retention policy; exceptions for legal obligation |
| **Rectification (Art. 16)** | Update endpoints for user profile, vessel, port call, etc. | RBAC and tenant isolation enforced |
| **Restriction (Art. 18)** | Manual process; flag account or data for restricted processing | Operational procedure |
| **Objection (Art. 21)** | Process via DPO/controller; cease processing where applicable | Per controller decision |

*Reference: EDD §13 — Compliance & GDPR*

---

## 6. Technical and Organizational Measures

| Measure | Implementation |
|---------|----------------|
| **Encryption at rest** | AES-256 for database and sensitive fields (EDD §6.1) |
| **Encryption in transit** | TLS 1.3 only; HSTS (EDD §6.1) |
| **RBAC** | Permissions (e.g. `vessel:read`, `da:approve`, `admin:users`); tenant-scoped (EDD §6.2) |
| **Tenant isolation** | All queries filtered by `tenant_id`; no cross-tenant access (EDD §3.3) |
| **Audit logging** | Append-only; who, what, when, minimal context; SIEM-ready (EDD §6.4) |
| **MFA** | TOTP for sensitive roles; MFA secret encrypted in DB (EDD §6.2) |
| **Secrets management** | Stored in secret manager; never in code or client payloads (EDD §6.1) |
| **Input validation** | Pydantic validation on all endpoints (EDD §6.3) |
| **Rate limiting** | Per-IP limits (SlowAPI); mitigates abuse (EDD §6.3) |

---

## 7. Document Version and Review Schedule

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | March 2026 | — | Initial GDPR processing records |

**Review schedule:** Annual review, or upon material change to processing activities, subprocessors, or legal requirements.

---

*End of GDPR Processing Records*
