# Task 5.11 — Runbooks (incidents, escalation, rollback)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Documented procedures for common incidents (e.g. high latency, queue backlog, auth issues, LLM failures), escalation, and rollback (EDD §5 scope).

## Scope

- **Incidents:** Runbooks for high latency, high error rate, queue backlog, auth/Login failures, LLM or email provider outage, DB/Redis connectivity, disk or memory pressure.
- **Steps:** How to diagnose (metrics, logs, traces); how to mitigate (scale, restart, disable feature, failover); when to escalate.
- **Escalation:** Who to call; when to escalate; how to hand off.
- **Rollback:** When to roll back (per go-live plan); steps to revert deploy or DNS; post-rollback verification.
- **Location:** Runbooks in repo or wiki; linked from alerts and onboarding doc.
- **Validation:** Where possible, runbook steps have been tested (e.g. in staging).

## Acceptance criteria

- [ ] Runbooks exist for critical failure modes and are linked from alerts or ops doc.
- [ ] Escalation path and rollback procedure are clear and agreed.
- [ ] At least one runbook has been validated (e.g. simulated incident in staging).
