# Task 1.21 — Role Management: Create & Edit Roles

**Epic:** [01-core-infrastructure](../epic.md)

---

## Objective

Enable admins to create new roles and edit existing roles (including permissions). Currently roles can only be listed; users cannot add or change permissions, leading to a chicken-and-egg problem (e.g. cannot add `da:read` to see Disbursements).

---

## Problem statement

- **Current state:** RoleList shows roles read-only. Backend has `POST /admin/roles` (create) but no update endpoint. No UI for create or edit.
- **Pain:** Admins cannot fix permission gaps (e.g. add `da:read` to a role). Users stuck with whatever permissions their role had at creation.
- **Goal:** Full role CRUD: create roles, edit role name and permissions.

---

## Scope

### 1. Backend

- **PUT /api/v1/admin/roles/{id}** — Update role (name, permissions). Requires `admin:roles`.
- **GET /api/v1/admin/roles/{id}** — Get single role (for edit form). Requires `admin:roles`.
- `admin_svc.update_role(db, tenant_id, role_id, data)` — update name and/or permissions.
- Schema: `RoleUpdate` with `name: str | None`, `permissions: list[str] | None`.

### 2. Frontend

- **RoleForm** — Create and edit roles (name, permissions as multi-select or tag input).
- **RoleList** — Add "New Role" button; add row click or "Edit" action to open RoleForm.
- Routes: `/admin/roles`, `/admin/roles/new`, `/admin/roles/:roleId/edit`.
- Known permissions list for UI (or fetch from API if we add a permissions manifest).

### 3. Permissions reference

Use for the permissions multi-select:

```
vessel:read, vessel:write
port_call:read, port_call:write
admin:users, admin:roles
ai:parse
da:read, da:write, da:approve, da:send
```

---

## Acceptance criteria

- [ ] Admin can create a new role with name and permissions via UI.
- [ ] Admin can edit an existing role (name, permissions) via UI.
- [ ] Admin can view a single role (GET /admin/roles/{id}) for the edit form.
- [ ] Permission changes take effect after user re-logs (JWT carries permissions from role).
- [ ] Cannot delete or edit system/default roles if we introduce that concept later (out of scope for now).

---

## Implementation notes

### Backend

```python
# schemas/admin.py
class RoleUpdate(BaseModel):
    name: str | None = None
    permissions: list[str] | None = None

# services/admin.py
async def update_role(db, tenant_id, role_id, data: RoleUpdate) -> Role | None
async def get_role(db, tenant_id, role_id) -> Role | None
```

### Frontend

- Reuse patterns from UserForm, CompanyForm (input, select, submit/cancel).
- Permissions: checkbox list or multi-select with known permission strings.
- Consider not allowing edit of the role the current user has (to avoid locking oneself out) — optional.

---

## Related code

- `backend/app/routers/admin.py` — add GET/PUT for roles/{id}
- `backend/app/services/admin.py` — add get_role, update_role
- `backend/app/schemas/admin.py` — add RoleUpdate
- `frontend/src/pages/admin/RoleList.tsx` — add New/Edit actions
- `frontend/src/pages/admin/RoleForm.tsx` — new file (create + edit)
- `frontend/src/router.tsx` — add routes for roles/new, roles/:roleId/edit

---

## Dependencies

- Task 1.17 (Admin UI) — existing RoleList, admin:roles permission.
- Task 1.10 (Admin service) — existing list_roles, create_role.
