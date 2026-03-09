# Task 5.1 — Production deployment (CI/CD, K8s, TLS, ingress)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Deploy production environment via CI/CD; Kubernetes with TLS termination, ingress, and rate limiting (EDD §10.2, §10.1).

## Scope

- **Pipeline:** Build, test, build Docker image, push to registry; deploy to production (Kubernetes apply or GitOps — Argo CD/Flux) (EDD §10.1).
- **Cluster:** Production namespace; backend Deployment (multiple replicas); workers Deployment; HPA (EDD §10.2).
- **Ingress:** TLS termination (certificates); route to backend; rate limiting at edge or ingress (EDD §10.2).
- **Secrets:** Not in code or image; from K8s Secrets or external secret manager (EDD §10.2).
- Rollback procedure: revert image or manifest; document steps.

## Acceptance criteria

- [ ] Production is deployed via pipeline; TLS and ingress are configured; traffic is served over HTTPS.
- [ ] Multiple replicas and HPA are in place; rate limiting is active.
- [ ] Rollback can be executed and verified; deployment and rollback are documented.
