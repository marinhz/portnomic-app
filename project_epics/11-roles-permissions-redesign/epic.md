# Epic 11 — Roles & Permissions Module Redesign

**Source:** User feedback — "Users don't understand what permissions to setup"  
**Duration (estimate):** 2–3 weeks

---

## Objective

Redesign the roles and permissions module so admins can easily understand and configure access control. The current flat list of technical permission strings (e.g. `da:read`, `vessel:write`) is confusing. Users need a module-based, user-friendly UI with clear labels and guidance.

---

## Problem statement

- **Current state:** RoleForm shows a flat list of ~15 permissions as checkboxes. No grouping, no descriptions, no context. Permissions use technical names (`da:approve`, `admin:roles`) that don't explain what they do.
- **User feedback:** "I don't understand what permissions to setup."
- **Goal:** Organize permissions by module/feature area, add human-readable labels and descriptions, and improve the overall UX of role management.

---

## Scope

### 1. Module-based permission grouping

- **Group permissions by feature area:**
  - **Vessels** — View vessels, Create/edit vessels
  - **Port calls** — View port calls, Create/edit port calls
  - **Disbursements (DA)** — View DAs, Create/edit DAs, Approve DAs, Send DAs
  - **AI & parsing** — Run AI parse on emails
  - **Admin** — Manage users, Manage roles
  - **Billing** — Manage billing and subscription
  - **Settings** — Edit tenant settings and integrations

- Each group is a collapsible section or card. Permissions within a group use friendly labels and optional tooltips/descriptions.

### 2. User-friendly permission labels

- Replace raw strings (`da:read`) with human-readable labels ("View disbursements").
- Add short descriptions or tooltips where helpful (e.g. "Approve DAs — Required to approve Proforma and Final DAs before dispatch").
- Consider role presets or templates (e.g. "Operations Manager", "Finance Only") to speed up setup.

### 3. UI improvements

- **RoleForm:** Module-based accordion or card layout; checkboxes with labels and descriptions; optional "Select all in module" for power users.
- **RoleList:** Show permission summary by module (e.g. "Vessels ✓, DA ✓, Admin ✗") instead of raw tags; improve scannability.
- **Onboarding:** Optional inline help or guided flow for first-time role creation.

### 4. Backend (if needed)

- **Permissions manifest API** (optional): `GET /api/v1/admin/permissions` — Returns grouped permissions with labels and descriptions. Enables dynamic UI and future extensibility.
- If not implemented, keep static grouping in frontend; backend permission strings unchanged.

---

## Out of scope (for now)

- Changing backend permission model or RBAC logic.
- Custom permissions per tenant.
- Permission inheritance or role hierarchies.
- Audit of who changed which role (separate epic).

---

## Tasks

- [Task 11.1](tasks/task-01-permissions-manifest-api.md) — Permissions manifest API (optional; enables dynamic UI)
- [Task 11.2](tasks/task-02-role-form-module-grouping.md) — RoleForm: module-based grouping, labels, descriptions
- [Task 11.3](tasks/task-03-role-list-permission-summary.md) — RoleList: permission summary by module
- [Task 11.4](tasks/task-04-role-presets-templates.md) — Role presets/templates (optional quick-start)

---

## Acceptance criteria

- [ ] Permissions are grouped by module (Vessels, Port calls, DA, AI, Admin, Billing, Settings) in the role form.
- [ ] Each permission shows a human-readable label (e.g. "View disbursements" instead of `da:read`).
- [ ] Optional descriptions or tooltips help admins understand what each permission does.
- [ ] Role list shows a clearer summary of what each role can do (by module).
- [ ] Admins report improved understanding of how to configure roles (qualitative feedback).

---

## Related code

- `frontend/src/pages/admin/RoleForm.tsx` — Current flat permission checkboxes
- `frontend/src/pages/admin/RoleList.tsx` — Current role list with permission tags
- `backend/app/routers/admin.py` — Admin API
- [Task 1.21](../01-core-infrastructure/tasks/task-21-role-management-crud.md) — Original role CRUD implementation
