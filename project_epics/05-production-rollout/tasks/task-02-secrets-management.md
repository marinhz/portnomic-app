# Task 5.2 — Secrets management (production)

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

All production secrets from Kubernetes Secrets or external secret manager; none in code or image (EDD §10.2, §10.1).

## Scope

- **Secrets:** DATABASE_URL, REDIS_URL, JWT_SECRET, LLM_API_KEY, SMTP/SENDGRID, STORAGE_*, etc. (EDD Appendix B).
- **Storage:** Kubernetes Secrets or external (e.g. HashiCorp Vault, cloud secret manager); injected into pods via env or volume.
- **Rotation:** Process for rotating secrets without downtime (or with planned restart); document who and how.
- **Access:** Only production pipeline and authorized ops can write production secrets; audit access if supported.

## Acceptance criteria

- [ ] No secrets in repo or Docker image; all loaded from secret store at runtime.
- [ ] Rotation process is documented and tested (e.g. JWT secret, DB password).
- [ ] Access to production secrets is restricted and audited where possible.
