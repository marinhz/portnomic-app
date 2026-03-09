# Task 6.1 — Mail connection entity and persistence

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Introduce a tenant-scoped mail connection entity and persist it in the database with encrypted credentials (OAuth tokens or IMAP password), so the system can support per-tenant mailbox connections.

## Scope

- New table `mail_connections` (or equivalent): id (UUID), tenant_id (FK), provider (enum: gmail | outlook | imap), display_email (nullable), encrypted credentials (e.g. JSON: access_token, refresh_token, expires_at for OAuth; or password for IMAP), imap_host / imap_port / imap_user (nullable, for IMAP), status (connected | error | disconnected), error_message (nullable), created_at, updated_at.
- Uniqueness: one row per (tenant_id, provider) or allow multiple per tenant (e.g. unique on tenant_id + provider + display_email); define in epic.
- Encryption: use same approach as MFA secret (key from settings/secret manager); encrypt before save, decrypt in service layer only.
- Alembic migration; no destructive changes to existing tables.
- Indexes: (tenant_id, status) for worker queries; tenant_id for API list.

## Acceptance criteria

- [ ] Migration creates `mail_connections` with required columns and FKs.
- [ ] Credentials column stores encrypted payload; key not in DB.
- [ ] Model and repository/service layer support create, get by tenant, get by id, update status/credentials, delete (disconnect).
