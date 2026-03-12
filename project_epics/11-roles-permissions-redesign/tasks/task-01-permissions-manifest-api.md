# Task 11.1 — Permissions Manifest API

**Epic:** [11-roles-permissions-redesign](../epic.md)

---

## Objective

Add an optional API endpoint that returns the full list of permissions grouped by module, with human-readable labels and descriptions. Enables a dynamic, maintainable UI and future extensibility.

---

## Scope

### Backend

- **GET /api/v1/admin/permissions** — Returns permissions manifest. Requires `admin:roles`.
- Response schema:

```json
{
  "data": {
    "modules": [
      {
        "id": "vessels",
        "label": "Vessels",
        "permissions": [
          { "id": "vessel:read", "label": "View vessels", "description": "See vessel list and details" },
          { "id": "vessel:write", "label": "Create & edit vessels", "description": "Add or modify vessels" }
        ]
      },
      {
        "id": "port_calls",
        "label": "Port calls",
        "permissions": [
          { "id": "port_call:read", "label": "View port calls", "description": "See port call list and details" },
          { "id": "port_call:write", "label": "Create & edit port calls", "description": "Add or modify port calls" }
        ]
      },
      {
        "id": "da",
        "label": "Disbursements (DA)",
        "permissions": [
          { "id": "da:read", "label": "View disbursements", "description": "See DA list and details" },
          { "id": "da:write", "label": "Create & edit DAs", "description": "Create Proforma/Final DAs" },
          { "id": "da:approve", "label": "Approve DAs", "description": "Approve DAs before dispatch" },
          { "id": "da:send", "label": "Send DAs", "description": "Dispatch DAs to recipients" }
        ]
      },
      {
        "id": "ai",
        "label": "AI & parsing",
        "permissions": [
          { "id": "ai:parse", "label": "Run AI parse", "description": "Trigger AI parsing on emails" }
        ]
      },
      {
        "id": "admin",
        "label": "Administration",
        "permissions": [
          { "id": "admin:users", "label": "Manage users", "description": "Create, edit, and remove users" },
          { "id": "admin:roles", "label": "Manage roles", "description": "Create and edit roles and permissions" }
        ]
      },
      {
        "id": "billing",
        "label": "Billing",
        "permissions": [
          { "id": "billing:manage", "label": "Manage billing", "description": "View and manage subscription" }
        ]
      },
      {
        "id": "settings",
        "label": "Settings",
        "permissions": [
          { "id": "settings:write", "label": "Edit settings", "description": "Configure tenant settings and integrations" }
        ]
      }
    ]
  }
}
```

- Implementation: Static manifest in backend (config or Python dict); no DB changes.

---

## Acceptance criteria

- [ ] `GET /api/v1/admin/permissions` returns grouped permissions with labels and descriptions.
- [ ] Endpoint requires `admin:roles`.
- [ ] Frontend can optionally fetch manifest instead of hardcoding; fallback to static list if API not used.

---

## Implementation notes

- Can be deferred; Task 11.2 can use a static manifest in the frontend initially.
- If implemented, frontend RoleForm fetches manifest on load and renders dynamically.
