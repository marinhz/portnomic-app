# Task 6.9 — Investigate Gmail sync bug (new emails not syncing)

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Investigate and fix the bug where users have new emails in their Gmail inbox but sync returns `ingested: 0` and emails do not appear in ShipFlow.

## Problem statement

- User connects Gmail via OAuth successfully.
- User has new/unread emails in Gmail INBOX.
- Manual "Sync now" or "Full sync" returns `{ ingested: 0 }`.
- Worker cron poll also does not ingest new emails.
- Emails never appear on the Emails page.

## Scope

- **Root cause analysis:** Identify why Gmail API list/fetch returns 0 messages or why all returned messages are treated as duplicates.
- **Gmail API query:** Current implementation uses `q=in:inbox` and optionally `after:YYYY/MM/DD`. Verify Gmail search syntax, `labelIds` vs `in:inbox`, and date format compatibility.
- **Sync cursor logic:** Review `last_sync_at` / `last_sync_cursor` usage; ensure incremental sync does not exclude valid new messages (e.g. race conditions, timezone, date boundary issues).
- **Duplicate detection:** Confirm `external_id` (e.g. `gmail-{id}`) is stable and not causing false duplicates.
- **Logging:** Ensure sufficient INFO-level logs to diagnose: messages returned by API vs. newly ingested vs. skipped as duplicate.
- **Fix:** Implement corrected sync logic and validate with real Gmail account.

## Acceptance criteria

- [ ] Root cause documented (Gmail query, cursor, or other).
- [ ] Fix implemented and verified with test Gmail account.
- [ ] New emails in INBOX are reliably ingested on sync (manual and worker).
- [ ] Logging shows: `Gmail list: ... returned N message(s)` and `ingested M` for debugging.
- [ ] Full sync and incremental sync both work as expected.

## Related code

- `backend/app/services/oauth_ingest.py` — `_poll_gmail`, Gmail API calls
- `backend/app/services/mail_connection.py` — `update_sync_cursor`, `reset_sync_state_for_tenant`
- `backend/app/routers/integrations.py` — `POST /sync` (manual and full sync)

---

## Root cause (resolved)

**Primary bug:** `pageToken` was used together with `after:YYYY/MM/DD` when `last_sync_at` existed. Gmail API page tokens are valid only for the exact query that produced them. After the first sync, the next run used `q=in:inbox after:YYYY/MM/DD` with a `pageToken` from the previous query (`q=in:inbox`). This invalid combination caused empty or wrong results.

**Secondary issues:**
- `after:YYYY/MM/DD` uses PST and date-only precision; Unix timestamp `after:<ts>` is more precise and timezone-safe.
- No logging for skipped duplicates, making it hard to tell if the API returned messages but they were all duplicates.

**Fix applied:**
1. When `last_sync_at` exists (incremental sync): do not use `pageToken`; use `q=in:inbox after:<unix_timestamp>`.
2. When incremental: persist `last_sync_cursor=None` (no page token for next run).
3. Use Unix timestamp for `after:` instead of `YYYY/MM/DD`.
4. Add logging: `Gmail: tenant=... ingested N, skipped M duplicate(s)`.
