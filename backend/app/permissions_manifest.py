"""Static permissions manifest for the admin UI.

Returns grouped permissions with human-readable labels and descriptions.
Used by GET /api/v1/admin/permissions.
"""

from app.schemas.admin import PermissionItem, PermissionModule

PERMISSIONS_MANIFEST: list[PermissionModule] = [
    PermissionModule(
        id="vessels",
        label="Vessels",
        permissions=[
            PermissionItem(
                id="vessel:read",
                label="View vessels",
                description="See vessel list and details",
            ),
            PermissionItem(
                id="vessel:write",
                label="Create & edit vessels",
                description="Add or modify vessels",
            ),
        ],
    ),
    PermissionModule(
        id="port_calls",
        label="Port calls",
        permissions=[
            PermissionItem(
                id="port_call:read",
                label="View port calls",
                description="See port call list and details",
            ),
            PermissionItem(
                id="port_call:write",
                label="Create & edit port calls",
                description="Add or modify port calls",
            ),
        ],
    ),
    PermissionModule(
        id="da",
        label="Disbursements (DA)",
        permissions=[
            PermissionItem(
                id="da:read",
                label="View disbursements",
                description="See DA list and details",
            ),
            PermissionItem(
                id="da:write",
                label="Create & edit DAs",
                description="Create Proforma/Final DAs",
            ),
            PermissionItem(
                id="da:approve",
                label="Approve DAs",
                description="Approve DAs before dispatch",
            ),
            PermissionItem(
                id="da:send",
                label="Send DAs",
                description="Dispatch DAs to recipients",
            ),
        ],
    ),
    PermissionModule(
        id="ai",
        label="AI & parsing",
        permissions=[
            PermissionItem(
                id="ai:parse",
                label="Run AI parse",
                description="Trigger AI parsing on emails",
            ),
        ],
    ),
    PermissionModule(
        id="admin",
        label="Administration",
        permissions=[
            PermissionItem(
                id="admin:users",
                label="Manage users",
                description="Create, edit, and remove users",
            ),
            PermissionItem(
                id="admin:roles",
                label="Manage roles",
                description="Create and edit roles and permissions",
            ),
        ],
    ),
    PermissionModule(
        id="billing",
        label="Billing",
        permissions=[
            PermissionItem(
                id="billing:manage",
                label="Manage billing",
                description="View and manage subscription",
            ),
        ],
    ),
    PermissionModule(
        id="settings",
        label="Settings",
        permissions=[
            PermissionItem(
                id="settings:write",
                label="Edit settings",
                description="Configure tenant settings and integrations",
            ),
        ],
    ),
]
