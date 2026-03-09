# Task 4.8 — GDPR: right to erasure

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Support right to erasure: soft-delete or anonymize user and PII; retain audit and legal hold where required (EDD §13).

## Scope

- **User erasure:** Soft-delete or anonymize user record (e.g. email, name); revoke sessions and tokens; retain audit log entries (anonymize user_id if required by policy).
- **PII in operational data:** Anonymize or redact PII in vessels, port calls, emails, DAs where legally required; retain data needed for legal/financial compliance (EDD §13).
- **Legal hold:** Do not erase data under legal hold; document process.
- **Processing records:** Logs of processing activities (including erasure requests) available for DPA/audits (EDD §13).
- API or admin flow to perform erasure; audit trail of erasure requests.

## Acceptance criteria

- [ ] Erasure request can be executed for a user; PII is removed or anonymized per policy.
- [ ] Audit and legal hold data are retained as required; legal hold overrides erasure.
- [ ] Process and scope are documented; DPA can review (EDD §13).
