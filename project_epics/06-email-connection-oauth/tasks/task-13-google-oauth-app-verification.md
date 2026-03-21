# Task 6.13 — Google OAuth App Verification

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Agent

Use the **Frontend** agent for any UI messaging changes. Backend changes (if any) require **fastapi-python** skill. This is primarily an **ops / business** task — Google Cloud Console configuration and submission.

---

## Objective

Resolve the "Google hasn't verified this app" warning that users see when connecting Gmail. Google shows this because the app requests sensitive scopes (`gmail.readonly`, `email`, `openid`) and has not completed Google's OAuth App Verification. Until verified, users see:

> Google hasn't verified this app  
> The app is requesting access to sensitive info in your Google Account. Until the developer (marinzapryanov@gmail.com) verifies this app with Google, you shouldn't use it.

Complete Google's verification process so users can connect Gmail without the unverified-app warning.

---

## Scope

### Google OAuth verification requirements

1. **Google Cloud Console**
   - Use the existing OAuth 2.0 Client (or create a new one for production).
   - Ensure OAuth consent screen is configured: app name, logo, support email, developer contact.

2. **Prerequisites for verification**
   - **Privacy Policy URL** — publicly accessible, describes data collected and how it's used (especially Gmail read access).
   - **Terms of Service URL** — if applicable.
   - **App homepage / website** — the application URL (e.g. `https://app.shipflow.io` or marketing site).
   - **Authorized domains** — verified in Search Console or via DNS; must include the domain hosting the OAuth app.
   - **Scopes justification** — document why each scope is needed (`gmail.readonly` for email ingest; `email`, `openid` for user identity).

3. **Verification submission**
   - In Google Cloud Console: APIs & Services → OAuth consent screen → "Publish app" → Submit for verification.
   - Provide a **video** or **screencast** showing the OAuth flow: user clicks Connect Gmail → Google consent → callback → app uses the connection (e.g. shows connected mailbox or ingested emails).
   - Provide a **written explanation** of how the app uses Gmail data (e.g. "Read-only access to inbox for parsing vessel-related emails into disbursement accounts").

4. **Post-verification**
   - Once approved, the "unverified app" warning is removed for all users.
   - If rejected, address feedback and resubmit.

### Optional UI improvements (low priority)

- Add a short note on the Integrations page for Gmail: e.g. "We use read-only access to parse vessel-related emails. Your data is encrypted and never shared."
- Consider a help link or tooltip explaining the verification status during the transition period.

---

## Acceptance criteria

- [ ] OAuth consent screen in Google Cloud Console is fully configured (name, logo, support email, developer contact).
- [ ] Privacy Policy is published and linked from OAuth consent screen.
- [ ] App homepage / website URL is set and domains are verified.
- [ ] Verification is submitted with required video and written justification.
- [ ] (If approved) Users connecting Gmail no longer see the "Google hasn't verified this app" warning.
- [ ] (Optional) Integrations page includes brief privacy/scope explanation for Gmail to build trust.

---

## Out of scope (for this task)

- Changing OAuth scopes (current scopes are minimal for read-only ingest).
- Microsoft OAuth verification (separate process for Outlook).
- Creating the Privacy Policy or Terms of Service content — these may exist elsewhere; link them or create if missing.

---

## Related code & config

- `backend/app/services/mail_connection.py` — `GOOGLE_SCOPES`, `build_google_auth_url`
- `frontend/src/pages/settings/IntegrationsPage.tsx` — Connect Gmail button
- `.env` — `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`
- Google Cloud Console: APIs & Services → OAuth consent screen → Credentials

---

## Dependencies

- Privacy Policy and Terms of Service (create or link existing).
- Domain verification (e.g. Search Console, DNS TXT).
- Production app URL for OAuth redirect and homepage.

---

## References

- [Google OAuth App Verification](https://support.google.com/cloud/answer/9110914)
- [OAuth consent screen configuration](https://console.cloud.google.com/apis/credentials/consent)
- [Sensitive scopes and restricted scopes](https://developers.google.com/identity/protocols/oauth2/scopes)
