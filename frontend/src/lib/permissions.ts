/**
 * Shared permission module mapping for RoleForm and RoleList.
 * Matches Task 11.2 module groups.
 */
export const PERMISSION_MODULES = [
  { id: "vessels", label: "Vessels", permissionIds: ["vessel:read", "vessel:write"] },
  { id: "port_calls", label: "Port calls", permissionIds: ["port_call:read", "port_call:write"] },
  { id: "da", label: "DA", permissionIds: ["da:read", "da:write", "da:approve", "da:send"] },
  { id: "ai", label: "AI", permissionIds: ["ai:parse"] },
  { id: "admin", label: "Admin", permissionIds: ["admin:users", "admin:roles"] },
  { id: "billing", label: "Billing", permissionIds: ["billing:manage"] },
  { id: "settings", label: "Settings", permissionIds: ["settings:write"] },
] as const;

export type PermissionModuleSummary = (typeof PERMISSION_MODULES)[number];

/**
 * Returns module-based summary for a role's permissions.
 * Each module shows ✓ if role has at least one permission, ✗ otherwise.
 */
export function getModuleSummary(permissions: string[]): { label: string; hasAccess: boolean }[] {
  return PERMISSION_MODULES.map((mod) => ({
    label: mod.label,
    hasAccess: mod.permissionIds.some((id) => permissions.includes(id)),
  }));
}
