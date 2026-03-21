# Task 6.14 — Add Privacy Policy and Google App Homepage Links to Login Page

**Epic:** [06-email-connection-oauth](../epic.md)

---

## Agent

Use the **Frontend** agent for this UI change. Reference **react-dev** and **tailwind-design-system** skills if needed.

---

## Objective

Add two footer links on the login page:

1. **Privacy Policy** — [https://portnomic.com/privacy-policy](https://portnomic.com/privacy-policy) — required by Google OAuth verification; good practice for user trust.
2. **Google App Homepage** — [https://support.google.com/cloud/answer/13807376?hl=en-GB](https://support.google.com/cloud/answer/13807376?hl=en-GB) — transparency about how the app meets OAuth requirements.

---

## Scope

### Implementation

- Add footer links on the login page (below the sign-in card or in a subtle footer area).
- Links:
  - Privacy Policy → `https://portnomic.com/privacy-policy`
  - App Homepage & verification → `https://support.google.com/cloud/answer/13807376?hl=en-GB`
- Both links should open in a new tab (`target="_blank"` with `rel="noopener noreferrer"`).
- Style: low-emphasis (e.g. small, muted text) so they don't distract from the primary login flow.
- Common pattern: "Privacy Policy · App Homepage" or stacked/grouped links.

### Reference

Google's OAuth App Homepage requirements include having a privacy policy link visible without login. The Portnomic privacy policy is at portnomic.com/privacy-policy.

---

## Acceptance criteria

- [ ] Login page includes a visible link to the Privacy Policy (https://portnomic.com/privacy-policy).
- [ ] Login page includes a visible link to the Google App Homepage documentation.
- [ ] Links open in a new tab with appropriate security attributes (`rel="noopener noreferrer"`).
- [ ] Link styling is subtle and does not compete with the sign-in form.
- [ ] Links remain visible on both the standard login form and MFA form.

---

## Related code

- `frontend/src/auth/LoginPage.tsx` — login and MFA forms

---

## References

- [Privacy Policy | Portnomic](https://portnomic.com/privacy-policy)
- [Google OAuth — App Homepage](https://support.google.com/cloud/answer/13807376?hl=en-GB)
- [Task 6.13 — Google OAuth App Verification](task-13-google-oauth-app-verification.md)
