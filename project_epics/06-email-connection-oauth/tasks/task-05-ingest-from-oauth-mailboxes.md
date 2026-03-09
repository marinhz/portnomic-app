# Task 6.5 — Ingest from OAuth mailboxes (worker)

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Extend the email ingest pipeline so the worker (or scheduled job) fetches new messages from tenant-connected OAuth mailboxes (Gmail API, Microsoft Graph) and optionally per-tenant IMAP, then persists and enqueues parse jobs.

## Scope

- For each tenant that has at least one mail_connection with status `connected`: obtain decrypted credentials; refresh OAuth tokens if needed (Task 6.4); fetch new messages since last sync (use stored cursor or “messages after date”).
- **Gmail:** Gmail API (list messages, get message body); map to internal Email format (subject, body, received_at, external_id); persist with tenant_id; enqueue parse job.
- **Microsoft:** Graph API Mail.Read (list messages, get content); same mapping and persist/enqueue.
- **IMAP:** For connections with provider=imap, use existing IMAP logic (or shared helper) with tenant-specific host/user/password; same persist/enqueue.
- Idempotency: (tenant_id, external_id) unique; do not duplicate emails or jobs.
- Last-sync cursor or timestamp per connection to avoid re-processing old messages; update after successful fetch.
- Keep existing global IMAP poll behavior if configured (e.g. when no per-tenant connections, or as fallback); document precedence (e.g. per-tenant over global for that tenant).

## Acceptance criteria

- [ ] Worker processes all tenants with connected mailboxes (Gmail, Outlook, IMAP).
- [ ] New messages are stored in Email table with correct tenant_id and enqueued for AI parse.
- [ ] Duplicate messages (same external_id per tenant) do not create duplicate records or jobs.
- [ ] OAuth token refresh is used when needed; failed refresh marks connection error and does not crash worker.
- [ ] Global IMAP (if configured) still works for default tenant or when no per-tenant connection exists.
