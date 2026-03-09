# Task 5.4 — Go-live plan (DNS, traffic, rollback, communication)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Document and execute go-live: DNS, traffic shift, rollback criteria, and communication so cutover is controlled and reversible.

## Scope

- **DNS:** Point production domain to ingress; TTL and cutover window; optional blue-green or canary.
- **Traffic shift:** How traffic is switched (e.g. DNS flip, load balancer); validation steps (smoke tests, health checks).
- **Rollback criteria:** Under what conditions to roll back (e.g. error rate, critical failure); who decides; how to roll back (revert DNS, revert deployment).
- **Communication:** Notify stakeholders of go-live window; status updates; support readiness (who is on call).
- **Post-go-live:** Monitoring for first 24–48 h; incident response ready.

## Acceptance criteria

- [ ] Go-live plan is written and agreed; includes DNS, traffic, rollback, and communication.
- [ ] Rollback has been tested (e.g. revert deploy or DNS); decision maker and steps are clear.
- [ ] Stakeholders and support are informed; go-live executed per plan with sign-off.
