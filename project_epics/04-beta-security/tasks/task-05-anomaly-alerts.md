# Task 4.5 — Anomaly alerts (failed logins, permission denied, API patterns)

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Define and implement alerts/dashboards for failed logins, permission denied spikes, and unusual API patterns (EDD §6.4).

## Scope

- **Failed logins:** Metric and alert when failure count exceeds threshold (per user or global) in a time window.
- **Permission denied (403):** Spike or repeated 403s per user/tenant; possible abuse or misconfiguration.
- **Unusual API patterns:** High rate, unusual endpoints, or anomaly detection if tooling available.
- Dashboards for security ops: login success/failure, 403 by endpoint, request rate by tenant/user.
- Integrate with existing metrics (Prometheus) and alerting channel.

## Acceptance criteria

- [ ] Alerts fire for excessive failed logins and (optionally) permission denied spikes.
- [ ] Dashboards give visibility into auth and access patterns; thresholds are documented.
- [ ] Alert recipients and runbook steps are defined.
