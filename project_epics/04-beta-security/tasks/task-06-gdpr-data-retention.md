# Task 4.6 — GDPR: data retention (configurable, purge/archive)

**Epic:** [04-beta-security](../epic.md)

---

## Objective

Configurable per-tenant data retention; automated purge or archive after retention period (EDD §13).

## Scope

- **Retention policy:** Per tenant (e.g. 7 years for financial records); configurable in tenant settings or admin.
- **Automation:** Scheduled job or worker that purges or archives data past retention (e.g. old audit logs, emails, soft-deleted records); retain audit and legal hold where required (EDD §13).
- **Audit logs:** Retention per compliance (e.g. 7 years); archive to cold storage if needed (EDD §5.4).
- Document retention policy and how to configure; avoid deleting data under legal hold.

## Acceptance criteria

- [ ] Retention is configurable per tenant (or global default); purge/archive job runs and respects policy.
- [ ] Audit logs and legally required data are not purged before retention; legal hold is respected.
- [ ] Process is documented for DPA and audits (EDD §13).
