# Task 5.6 — Alerting (availability, errors, latency, queue, dependencies)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Configure thresholds and alerts for availability (NFR-1 99.5%), errors, latency, queue backlog, and dependency health (EDD §2.3, §11.1).

## Scope

- **Availability:** Alert when uptime or health check failure rate indicates breach of 99.5% (excluding planned maintenance) (EDD §2.3).
- **Errors:** Error rate above threshold (e.g. 5xx, 4xx) by endpoint or globally.
- **Latency:** p95 above target (e.g. 500 ms for reads); AI parse or DA generation timeout.
- **Queue:** Backlog depth above threshold; worker down or stuck.
- **Dependencies:** DB, Redis, LLM, or email provider unreachable or degraded.
- **Channels:** Alerts to PagerDuty, Slack, email, or equivalent; escalation path; avoid alert fatigue (thresholds and grouping).
- **Runbooks:** Link or embed runbook steps in alert payloads where possible.

## Acceptance criteria

- [ ] Alerts are configured and fire when conditions are met; tested with synthetic failure.
- [ ] On-call or support receives alerts; escalation path is clear.
- [ ] Thresholds and alert names are documented; runbooks linked for critical alerts.
