# Task 7.9 — Bug: Login page — wrong credentials error not shown, input text not visible

**Epic:** [07-ux-ui-polish](../epic.md)

**Type:** Bug

---

## Objective

Fix the login page so that (1) users see a clear error when credentials are wrong, and (2) text entered in email/password inputs is clearly visible.

---

## Problem statement

- **User report:** After entering wrong credentials the user doesn’t see an error, and there are problems with the visual input — text is not visible.
- **Expected:**
  - On invalid login, a visible error message (e.g. “Invalid email or password”) is shown near the form.
  - Email and password input text (and placeholders) are clearly visible and readable.
- **Actual:**
  - Error feedback after wrong credentials is missing or not visible.
  - Input text (typed or placeholder) has poor visibility or appears invisible.

---

## Scenario

1. User goes to the login page (e.g. `/login`).
2. User enters invalid email/password and submits.
3. **Observed:** No error message appears (or it’s not noticeable).
4. **Observed:** While typing in the email or password field, the text is hard to see or not visible.

---

## Scope

- **Error not shown:**
  - Confirm backend returns a clear error payload for invalid credentials and that the frontend maps it correctly (e.g. `ApiError.message` in `AuthContext`).
  - Ensure the login page displays the error state (e.g. the existing `error` block is rendered and visible — check contrast, layout, overflow, or conditional rendering).
  - If the API returns a different shape or status, adapt the client so a user-friendly message is always shown on failure.
- **Input text not visible:**
  - Ensure inputs have explicit, accessible text and placeholder color (e.g. dark text on light background) and sufficient contrast.
  - Check for overrides from global or theme styles that make input text too light or same as background.
  - Verify both email and password fields (and MFA code field if applicable) have readable text.
- **Verification:** Wrong credentials show a visible error; typed and placeholder text are clearly visible in all login inputs.

---

## Acceptance criteria

- [ ] When login fails (wrong credentials or server error), a clear error message is visible on the login page (inline and/or toast, as per design).
- [ ] Error message is readable (sufficient contrast, not hidden by layout or overflow).
- [ ] Email and password input text (and placeholder) are clearly visible with sufficient contrast.
- [ ] MFA code input (if used) also has visible text and placeholder.
- [ ] No regression in successful login or MFA flow.

---

## Related code

- `frontend/src/auth/LoginPage.tsx` — login form, error display (`error` state, red banner), input `inputClass` styling
- `frontend/src/auth/AuthContext.tsx` — `login()` and `completeMfa()` error handling, `LoginResult` / `MfaResult` and `ApiError.message`
- `frontend/src/api/client.ts` — `ApiError` and how API errors are mapped to messages
- Login route (e.g. in `frontend/src/router.tsx`)

---

## Dependencies

- Task 7.1 (shadcn, Sonner) — optional: consider using Sonner for login errors if aligning with rest of app.
- Auth/API contract for `/auth/login` (backend error response shape).
