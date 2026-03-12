# Task 11.4 — Role Presets / Templates (Optional)

**Epic:** [11-roles-permissions-redesign](../epic.md)

---

## Objective

Add optional role presets (templates) so admins can quickly create common roles (e.g. "Operations Manager", "Finance Only", "Viewer") with one click, then adjust as needed. Reduces setup time and guides new admins.

---

## Scope

### Frontend

- **Preset buttons or dropdown:** When creating a new role, show "Start from template" with presets:
  - **Operations Manager** — Vessels, Port calls, DA (read/write/approve/send), AI parse
  - **Finance Only** — DA (read/write/approve/send), Billing
  - **Viewer** — Vessels (read), Port calls (read), DA (read)
  - **Admin** — All permissions
- **Behavior:** Selecting a preset pre-fills the permissions checkboxes; admin can still modify.
- **Edit mode:** Presets only apply when creating; editing an existing role does not show presets (or show as "Reset to template" option).

### Backend

- No changes; presets are frontend-only. Permissions are still sent as a list of IDs.

---

## Acceptance criteria

- [ ] "New Role" form offers preset templates.
- [ ] Selecting a preset pre-fills permissions; admin can adjust.
- [ ] At least 3–4 useful presets (Operations Manager, Finance, Viewer, Admin).

---

## Priority

Optional / nice-to-have. Can be deferred if time is limited.
