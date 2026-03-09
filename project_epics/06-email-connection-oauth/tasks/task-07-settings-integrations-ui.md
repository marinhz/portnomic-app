# Task 6.7 — Settings / Integrations UI

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Objective

Add a Settings (or Integrations) page in the frontend where tenant admins can see connected mailboxes and start OAuth flows to connect Gmail or Outlook.

## Scope

- New route: e.g. `/settings/integrations` or `/settings/email` inside the protected app layout (same sidebar/nav as other app pages). Add to router and optionally to sidebar nav (e.g. “Settings” or “Integrations”).
- **Page content:** Section “Email for ingest” (or “Connected mailboxes”): list of connections from GET /api/v1/integrations/email — show provider (Gmail/Outlook/IMAP), display email or “Connected”, status (connected / error); “Disconnect” button per row with confirmation. Buttons: “Connect Gmail”, “Connect Outlook” (and optionally “Add IMAP” — see Task 6.8).
- “Connect Gmail” / “Connect Outlook”: frontend navigates to backend initiate URL (e.g. GET /api/v1/integrations/email/connect?provider=gmail) so the browser is redirected to the provider; after OAuth, backend callback redirects back to this page with success or error (e.g. query param `?email=connected` or `?error=access_denied`); frontend shows toast or inline message and refetches list.
- Permissions: show page only to users with permission to manage integrations (e.g. tenant admin); otherwise redirect or hide menu entry.
- Styling: consistent with existing app (Tailwind, layout); clear labels and loading/error states.

## Acceptance criteria

- [ ] User with required role can open Settings/Integrations and see the email section.
- [ ] List shows existing connections (provider, email/name, status); Disconnect works with confirmation.
- [ ] “Connect Gmail” and “Connect Outlook” trigger OAuth redirect; return to page with success and updated list.
- [ ] Error on callback (e.g. user denied) shows message on page; no crash.
- [ ] Users without permission do not see the page or cannot access it (403 or redirect).
