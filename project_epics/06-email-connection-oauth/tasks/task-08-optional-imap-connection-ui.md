# Task 6.8 — Optional: IMAP connection via UI

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Allow tenant admins to add an IMAP mailbox connection from the Settings/Integrations UI (host, port, user, password) as an alternative to OAuth, so tenants without Gmail/Outlook can still connect a mailbox.

## Scope

- **API:** POST /api/v1/integrations/email/imap — Body: imap_host, imap_port, imap_user, imap_password (or secure field); validate and create mail_connection with provider=imap; store password encrypted. Permission: same as connect (e.g. integrations:write). Optional: test connection before save (quick IMAP login).
- **Frontend:** On Integrations page, “Add IMAP” button opens a form (or modal): host, port, username, password; submit calls POST; on success add to list and clear form. Passwords not shown in list (display as “IMAP (user@host)” or similar).
- Worker already uses per-tenant IMAP connections (Task 6.5); this task only adds the API and UI to create them.
- Security: password encrypted at rest; no password in list/detail API response; consider rate limit on add to prevent abuse.

## Acceptance criteria

- [ ] Tenant admin can submit IMAP credentials via form; connection is created and appears in list.
- [ ] Stored password is encrypted; worker can decrypt and use for poll.
- [ ] List/detail never return password; display only safe identifier (e.g. user@host).
- [ ] Optional: “Test connection” validates credentials before saving.
