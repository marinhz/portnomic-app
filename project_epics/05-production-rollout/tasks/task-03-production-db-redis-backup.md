# Task 5.3 — Production DB and Redis; backup/restore

**Epic:** [05-production-rollout](../epic.md)

---

## Objective

Production PostgreSQL and Redis; migrations applied; backup and restore verified (EDD §10.2).

## Scope

- **PostgreSQL:** Primary (and read replicas if used); production DB created and migrated via Alembic; connection limits and timeouts configured.
- **Redis:** Production instance; used for cache and queue; persistence and memory limits per need.
- **Backup:** Automated backups (e.g. daily); retention policy; backup stored off-cluster or in separate region.
- **Restore:** Restore procedure tested (e.g. to staging); document RTO/RPO and steps.
- **Data integrity:** Verify no test data in production; sanitize if needed.

## Acceptance criteria

- [ ] Production DB and Redis are provisioned and migrations applied successfully.
- [ ] Backups run on schedule; at least one restore has been tested and documented.
- [ ] RTO/RPO and backup retention are documented; team knows how to restore.
