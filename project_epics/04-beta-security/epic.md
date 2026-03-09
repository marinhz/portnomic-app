# Epic 4 — Beta & Security

**Source:** SHIPFLOW_AI_Engineering_Design_Document.md, Implementation Roadmap Phase 4  
**Duration (estimate):** 2 weeks

---

## Objective

Harden the system for beta and production: penetration testing, audit review, GDPR alignment (export/erasure), and performance tuning so that security, compliance, and NFRs are met.

---

## Scope

### Security verification

- **Penetration test:** External or internal pen test; remediate findings (EDD §12 threat model).
- **Threat mitigations:** Confirm unauthorized access (auth/MFA/RBAC/tenant isolation), data leakage (encryption, no cross-tenant), AI manipulation (input sanitization, output validation, audit), financial fraud (approval workflow, audit), abuse/DoS (rate limiting, quotas, monitoring) (EDD §12).
- **Application security:** Input validation (Pydantic), no sensitive data in errors, CORS whitelist, rate limiting per tenant/user (EDD §6.3).

### Audit review

- **Audit log:** Every state-changing action logged; append-only; SIEM-ready format (EDD §6.4).
- **Review:** Ensure who, what, when, resource_type, resource_id, and minimal context are captured; correlation IDs for tracing (EDD §6.4, §11.2).
- **Anomaly:** Failed logins, permission denied spikes, unusual API patterns — alerts/dashboards where feasible (EDD §6.4).

### GDPR checks

- **Data retention:** Configurable per tenant; automated purge or archive after retention (EDD §13).
- **Right of access / portability:** Export of user and operational data (e.g. JSON/CSV) via secure download (EDD §13, FR-9).
- **Right to erasure:** Soft-delete or anonymize user and PII; retain audit and legal hold where required (EDD §13).
- **Processing records:** Logs of processing activities available for DPA/audits (EDD §13).
- **Subprocessors:** LLM and email providers; DPAs/SCCs where applicable (EDD §13).

### Performance tuning

- **NFR-2:** API latency p95 &lt; 500 ms for read endpoints (EDD §2.3).
- **NFR-3:** AI parse latency p95 &lt; 30 s per email (EDD §2.3).
- **Optimisation:** DB indexes, query tuning, read replicas for read-heavy endpoints; Redis cache-aside for reference data; worker scaling and queue tuning (EDD §4.3, §11).

### Observability (baseline for beta)

- **Health:** `/health` (liveness), `/ready` (DB + Redis + queue) for K8s (EDD §11.4).
- **Logging:** Structured JSON; request_id, tenant_id, user_id, correlation_id; no passwords/tokens/PII (EDD §11.2).
- **Metrics:** Key metrics defined (request rate, latency, error rate, AI parse duration/success, queue depth) (EDD §11.1).

---

## Out of scope

- Full production rollout and runbooks (Epic 5).
- New feature development unless required to meet security/compliance.

---

## Acceptance criteria

- [ ] Penetration test completed; critical/high findings remediated or accepted with mitigation plan.
- [ ] Audit log coverage and format verified; correlation IDs and SIEM readiness confirmed.
- [ ] Data export (access/portability) and erasure paths implemented and tested; retention and processing records documented.
- [ ] API and AI parse latency meet or approach NFR targets; DB/Redis and worker scaling validated.
- [ ] Health and readiness endpoints in place; structured logging and key metrics available for beta.

---

## EDD references

- §2.3 Non-functional requirements  
- §6 Security design (encryption, auth, application security, audit)  
- §11 Observability & resilience  
- §12 Threat model & risk mitigation  
- §13 Compliance & GDPR
