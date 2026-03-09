# Task 4.4 — Audit log coverage and format review

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Ensure every state-changing action is logged; format is append-only and SIEM-ready (EDD §6.4, §11.2).

## Scope

- **Coverage:** Create/update/delete for users, roles, vessels, port calls, DAs, tariffs; auth events (login, MFA, failure); approve and send DA.
- **Format:** who (user_id), what (action), when (timestamp), resource_type, resource_id, minimal context (payload); no passwords/tokens/PII (EDD §6.4).
- **Immutability:** Append-only store; no updates/deletes to audit records.
- **SIEM:** Structured (e.g. JSON); correlation_id for request tracing; export or forward to central logging.
- Review and add any missing audit points; validate format.

## Acceptance criteria

- [ ] All state-changing actions produce an audit record; list is documented and reviewed.
- [ ] Log format is consistent and SIEM-ready; correlation_id present where applicable.
- [ ] No sensitive data in audit payloads; logs are immutable.
