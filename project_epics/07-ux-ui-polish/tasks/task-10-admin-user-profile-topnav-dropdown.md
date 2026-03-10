# Task 7.10 — Admin in user profile dropdown, remove sidebar user info

**Epic:** [07-ux-ui-polish](../epic.md)

---

## Objective

1. Move the Admin section from the sidebar to the top navigation bar, inside a user profile dropdown.
2. Remove the user info block (avatar + email) from the bottom of the sidebar.

---

## Problem statement

- **Current state:** Admin links (Users, Roles, Companies) live in the sidebar under an "Admin" section. User avatar and email are duplicated: in the topnav and at the bottom of the sidebar.
- **Pain:** Admin features clutter the sidebar; user info at the bottom of the sidebar is redundant with the topnav and consumes vertical space.
- **Goal:** Admin access via user profile dropdown in topnav; sidebar focused on navigation only; single place for user identity in the header.

---

## Scope

### 1. Add user profile dropdown in topnav

- **Location:** `frontend/src/layout/AppLayout.tsx` — header section.
- **Replace:** The current inline user avatar + email + Logout with a **dropdown menu** triggered by clicking the avatar/email area.
- **Dropdown contents:**
  - User email (display only, non-clickable or as header)
  - Link to Profile (`/settings/profile`)
  - **Admin section** (only if user has admin permissions):
    - Users (`/admin/users`) — if `admin:users`
    - Roles (`/admin/roles`) — if `admin:roles`
    - Companies (`/admin/companies`) — if `is_platform_admin`
  - Divider
  - Logout button
- **Implementation:** Use shadcn `DropdownMenu` (or equivalent) for consistent styling and accessibility.

### 2. Remove Admin section from sidebar

- **Location:** `frontend/src/layout/Sidebar.tsx`.
- **Remove:** The entire Admin block (lines ~229–256):
  - `SectionDivider label="Admin"`
  - NavItems for Users, Roles, Companies
- **Keep:** All other sidebar nav items unchanged (Operations, Inbox & Reports, Settings).

### 3. Remove user info from bottom of sidebar

- **Location:** `frontend/src/layout/Sidebar.tsx`.
- **Remove:** The user block at the bottom (lines ~293–321):
  - Avatar, email display, and tooltip
- **Result:** Sidebar ends with the collapse toggle (if present) or the last nav section. No user info in sidebar.

---

## Acceptance criteria

### User profile dropdown

- [ ] Clicking avatar/email in topnav opens a dropdown menu.
- [ ] Dropdown shows user email (or "Profile" header).
- [ ] Dropdown includes link to Profile (`/settings/profile`).
- [ ] Admin links (Users, Roles, Companies) appear in dropdown only when user has respective permissions.
- [ ] Logout button is in dropdown and works correctly.
- [ ] Dropdown closes on item click or outside click.
- [ ] Keyboard accessible (focus, Enter/Space to open, Escape to close).

### Sidebar changes

- [ ] Admin section (Users, Roles, Companies) removed from sidebar.
- [ ] User info block (avatar + email) removed from bottom of sidebar.
- [ ] Sidebar layout remains correct; collapse toggle (if present) is the last element.
- [ ] No regression in permission-based visibility for admin links (now in dropdown).

### Visual and UX

- [ ] Topnav remains clean; dropdown does not cause layout shift.
- [ ] Mobile: dropdown works from topnav (hamburger still opens sidebar).
- [ ] Icons for admin items in dropdown (Users, Roles, Companies) for consistency.

---

## Implementation notes

### Dropdown structure (example)

```tsx
// AppLayout header — replace inline user + Logout with:
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <button className="flex items-center gap-3 rounded-lg px-2 py-1.5 ...">
      <div className="h-8 w-8 rounded-full bg-mint-100 ...">
        {user?.email?.charAt(0).toUpperCase()}
      </div>
      <span className="hidden sm:inline">{user?.email}</span>
      <ChevronDown className="size-4" />
    </button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end" className="w-56">
    <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem asChild>
      <Link to="/settings/profile">Profile</Link>
    </DropdownMenuItem>
    {showAdmin && (
      <>
        <DropdownMenuSeparator />
        <DropdownMenuLabel>Admin</DropdownMenuLabel>
        {hasAdminUsers && <DropdownMenuItem asChild><Link to="/admin/users">Users</Link></DropdownMenuItem>}
        {hasAdminRoles && <DropdownMenuItem asChild><Link to="/admin/roles">Roles</Link></DropdownMenuItem>}
        {isPlatformAdmin && <DropdownMenuItem asChild><Link to="/admin/companies">Companies</Link></DropdownMenuItem>}
      </>
    )}
    <DropdownMenuSeparator />
    <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

### Permission logic

- Reuse existing permission checks from `Sidebar.tsx`: `hasAdminUsers`, `hasAdminRoles`, `isPlatformAdmin`, `showAdmin`.
- These can be moved to a shared hook (e.g. `useNavPermissions`) or duplicated in `AppLayout` for simplicity.

---

## Related code

- `frontend/src/layout/AppLayout.tsx` — topnav, user dropdown
- `frontend/src/layout/Sidebar.tsx` — remove Admin section and user block
- `frontend/src/components/ui/dropdown-menu.tsx` — shadcn DropdownMenu (if present)

---

## Dependencies

- **Task 7.1** — shadcn components (DropdownMenu) and Lucide icons.
- **Task 7.7** — topnav structure (theme toggle remains; user area becomes dropdown).

---

## Out of scope (for now)

- Moving Settings (Integrations, AI Settings, Billing) to dropdown — only Admin moves.
- Changing route URLs for admin pages.
- Adding "Switch account" or other profile actions.
