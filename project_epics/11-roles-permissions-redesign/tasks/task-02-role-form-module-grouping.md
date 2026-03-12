# Task 11.2 — RoleForm: Module-Based Grouping, Labels, Descriptions

**Epic:** [11-roles-permissions-redesign](../epic.md)

---

## Objective

Redesign the RoleForm so permissions are grouped by module (Vessels, Port calls, DA, AI, Admin, Billing, Settings) with human-readable labels and optional descriptions. Replace the flat checkbox list with a clearer, module-based layout.

---

## Problem statement

- **Current:** Flat list of technical strings (`da:read`, `vessel:write`) — users don't understand what to select.
- **Goal:** Grouped sections with labels like "View disbursements" and "Create & edit vessels"; optional tooltips for clarity.

---

## Scope

### Frontend

- **Permission manifest:** Define module groups and permission metadata (id, label, description) — either static in frontend or fetched from Task 11.1 API.
- **Layout:** Use collapsible sections (Accordion) or cards per module. Each section shows module name and its permissions as checkboxes with labels.
- **Labels:** Display "View disbursements" instead of `da:read`; keep `da:read` as the value sent to API.
- **Descriptions:** Show as tooltip (hover) or helper text below each permission.
- **Select-all:** Optional "Select all" per module for power users.
- **Backward compatible:** Continue sending permission IDs (`da:read`, etc.) to backend; no API changes.

### Module groups (reference)

| Module | Permissions |
|--------|-------------|
| Vessels | vessel:read, vessel:write |
| Port calls | port_call:read, port_call:write |
| Disbursements (DA) | da:read, da:write, da:approve, da:send |
| AI & parsing | ai:parse |
| Administration | admin:users, admin:roles |
| Billing | billing:manage |
| Settings | settings:write |

---

## Acceptance criteria

- [ ] Permissions are grouped by module in the role form.
- [ ] Each permission shows a human-readable label (e.g. "View disbursements").
- [ ] Descriptions available via tooltip or helper text.
- [ ] Role create/edit still works; backend receives correct permission IDs.
- [ ] UI is more scannable and understandable than the current flat list.

---

## Related code

- `frontend/src/pages/admin/RoleForm.tsx` — Current implementation with `KNOWN_PERMISSIONS` flat list
