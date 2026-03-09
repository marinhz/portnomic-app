# Task 3.8 — Email dispatch worker

**Epic:** [03-financial-automation](../epic.md)

---

## Objective

Send DA by email: PDF attachment, body from template; to addresses from port call or tenant config; SMTP or transactional API (EDD §9.3, §7.4).

## Scope

- Worker task: input DA id; ensure PDF exists (or trigger PDF task first); load to addresses (port call or tenant config); build email with template body and PDF attachment; send via SMTP or SendGrid/SES.
- On success: set DA status = sent; set sent_at; audit log (user, timestamp, DA id).
- Configuration: SMTP_* or SENDGRID_API_KEY; template storage.
- Retries for transient send failures; alert on permanent failure.

## Acceptance criteria

- [ ] Email is sent with PDF attached; DA status and sent_at updated; audit logged.
- [ ] To addresses and template are configurable; no secrets in templates.
- [ ] Failure handling does not mark DA as sent; operator can retry.
