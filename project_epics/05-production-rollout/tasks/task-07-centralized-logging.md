# Task 5.7 — Centralized logging (ELK or equivalent, retention)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Aggregate production logs to centralized system (e.g. ELK); retention and search for operations and compliance (EDD §11.2).

## Scope

- **Aggregation:** Logs from backend and workers shipped to central store (e.g. Elasticsearch, Loki, or cloud logging); structured JSON (EDD §11.2).
- **Retention:** Retention policy (e.g. 30–90 days hot, then archive); align with compliance (audit logs may have longer retention) (EDD §5.4).
- **Search:** Ops can search by request_id, tenant_id, user_id, correlation_id, level, time range.
- **Sensitive data:** No passwords, tokens, or PII in logs; redact in pipeline if needed (EDD §11.2).
- **Cost and access:** Access control; avoid over-retention that drives cost.

## Acceptance criteria

- [ ] Production logs are in centralized store; searchable by key fields.
- [ ] Retention is configured and documented; audit requirements are met.
- [ ] Access is restricted; no sensitive data in plain text in logs.
