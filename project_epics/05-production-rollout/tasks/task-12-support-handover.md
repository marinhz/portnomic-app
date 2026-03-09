# Task 5.12 — Support handover (documentation, knowledge transfer)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Hand over to support/ops: documentation, knowledge transfer, and clear ownership of monitoring and incident response (EDD §5 scope).

## Scope

- **Documentation:** Runbooks (Task 5.11); architecture overview; key env vars and secrets (references only, no values); support contacts; escalation path.
- **Knowledge transfer:** Session(s) with support/ops: how to access dashboards, logs, traces; how to interpret alerts; how to run runbooks; who owns what.
- **Access:** Support has access to monitoring, logs, and (if applicable) staging; no production secrets in shared docs.
- **Ownership:** Who is on call; who owns incidents vs feature requests; SLA or response expectations if applicable.
- **Handover checklist:** Sign-off that support has received docs, access, and training.

## Acceptance criteria

- [ ] Documentation set is complete and handed to support; contacts and escalation are clear.
- [ ] Knowledge transfer has been done; support can use dashboards, logs, and runbooks.
- [ ] Ownership of monitoring and incident response is agreed and documented.
