# Task 1.23 — User profile system

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Add a user profile system so logged-in users can view their account info, change their password, and manage MFA for their own account. Currently the app shows only email + avatar in the topnav with no dedicated profile page or self-service account management.

---

## Problem statement

- **Current state:** Users see their email and avatar in the topnav but have no way to view or edit their profile. Admin can manage users via Admin → Users, but regular users cannot change their own password or manage MFA.
- **Pain:** Users cannot self-serve password changes; MFA setup/disable requires admin intervention or is unclear.
- **Goal:** A profile page where users can view account info, change password, and manage MFA.

---

## Scope

### 1. Profile page (view)

- **Route:** `/settings/profile` (under Settings, alongside Integrations, Billing, AI).
- **Display (read-only):**
  - Email
  - Role name (resolve from `role_id` via API or include in `/auth/me`)
  - MFA status (enabled / disabled)
  - Account created date (if available from backend)
  - Last login (if available)
- **Layout:** Card-based, consistent with other settings pages (Integrations, Billing). Use shadcn Card, consistent spacing.

### 2. Change password

- **Form:** Current password, new password, confirm new password.
- **Validation:** New password meets policy (min length, complexity if defined); confirm matches new.
- **API:** New endpoint `POST /auth/change-password`:
  - Body: `{ "current_password": str, "new_password": str }`
  - Requires JWT; validates `current_password` against stored hash; updates user's `password_hash`.
  - Returns 204 on success; 400 if current password wrong or policy violated.
- **UX:** Success toast; optionally clear form. No redirect required.

### 3. MFA management (own account)

- **If MFA disabled:** Show "Enable MFA" button; link to existing MFA setup flow (if present) or implement:
  - `GET /auth/mfa/setup` → returns `{ secret, provisioning_uri }` for TOTP
  - User scans QR in authenticator app; enters code
  - `POST /auth/mfa/confirm` with code → enables MFA
- **If MFA enabled:** Show "Disable MFA" with confirmation (require current password or TOTP code for security).
- **Note:** Check if MFA setup/disable endpoints already exist (Task 1.5); reuse or add as needed.

### 4. Navigation and entry points

- **Sidebar:** Add "Profile" under Settings section (or "Account" if preferred), linking to `/settings/profile`.
- **Topnav:** Make avatar/email clickable to open dropdown with "Profile" and "Logout" (optional UX improvement; can be follow-up).

---

## Acceptance criteria

### Profile page

- [ ] Profile page at `/settings/profile` displays email, role, MFA status.
- [ ] Page uses shadcn components and matches Settings section styling.
- [ ] Profile page is linked from Sidebar under Settings.

### Change password

- [ ] Change password form with current, new, confirm fields.
- [ ] `POST /auth/change-password` endpoint implemented; validates current password and updates hash.
- [ ] Success toast on password change; form clears.
- [ ] Invalid current password shows clear error without leaking info.

### MFA management

- [ ] User can enable MFA from profile (setup flow with QR/code).
- [ ] User can disable MFA from profile (with confirmation).
- [ ] MFA status displayed correctly on profile.

### Security

- [ ] Change password and MFA actions require valid JWT.
- [ ] No sensitive data in URL or client-side logs.

---

## Implementation notes

### Backend: change password endpoint

```python
# app/routers/auth.py
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    # Fetch user, verify current_password, hash new_password, update
    ...
```

### Frontend: profile page structure

```tsx
// frontend/src/pages/settings/ProfilePage.tsx
// - Card with user info (email, role, mfa_enabled)
// - Card with Change password form
// - Card with MFA enable/disable section
```

### Router update

```tsx
// Add to router.tsx under settings
{ path: "settings/profile", Component: ProfilePage },
```

### Sidebar update

Add NavItem for Profile under Settings section (see `Sidebar.tsx`).

---

## Related code

- `frontend/src/layout/AppLayout.tsx` — topnav user display
- `frontend/src/layout/Sidebar.tsx` — Settings nav items
- `frontend/src/auth/AuthContext.tsx` — `user` from `/auth/me`
- `frontend/src/api/types.ts` — `CurrentUser` type
- `backend/app/routers/auth.py` — auth endpoints
- `backend/app/schemas/auth.py` — auth schemas
- `backend/app/services/auth.py` — `hash_password`, `authenticate_user`

---

## Dependencies

- **Task 1.5** (MFA) — MFA setup/disable flow; reuse or extend.
- **Task 1.14** (Auth UI) — Login/MFA forms; same patterns for profile forms.
- **Task 7.1** (shadcn, Lucide) — UI components for profile page.

---

## Out of scope (for now)

- Display name or avatar upload — would require User schema changes.
- Email change — requires verification flow; defer.
- Profile editing beyond password and MFA.
- Topnav avatar dropdown → Profile link (optional enhancement).
