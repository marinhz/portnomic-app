# Task 5.13 — Terraform production (IaC, pipeline)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Production infrastructure managed as code (Terraform); separate state/workspaces for dev, staging, prod; changes applied via pipeline with review (EDD §10.3).

## Scope

- **Terraform modules:** Network, cluster (or managed K8s), DB, Redis, DNS, certificates; reuse across envs (EDD §10.3).
- **State:** Separate state (or workspaces) for dev, staging, prod; state stored remotely (e.g. S3 + lock).
- **Pipeline:** Terraform plan and apply in CI; apply requires review (e.g. PR approval); destructive changes require explicit approval (EDD §10.3).
- **Secrets:** Terraform does not store secret values in state; use variables or external secret store for sensitive inputs.
- **Documentation:** How to run plan/apply; who can approve; what to do for destructive changes.

## Acceptance criteria

- [ ] Production infra is defined in Terraform; state is isolated and locked.
- [ ] Changes go through pipeline; apply is reviewed; destructive changes have extra gate.
- [ ] Runbook for Terraform (plan, apply, rollback) is available; team can safely make infra changes.
