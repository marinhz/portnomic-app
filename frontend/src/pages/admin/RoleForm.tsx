import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  RoleResponse,
  RoleCreate,
  RoleUpdate,
  PermissionModule,
  PermissionsManifest,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

/** Static fallback manifest when API is unavailable. */
const FALLBACK_MANIFEST: PermissionsManifest = {
  modules: [
    {
      id: "vessels",
      label: "Vessels",
      permissions: [
        { id: "vessel:read", label: "View vessels", description: "See vessel list and details" },
        { id: "vessel:write", label: "Create & edit vessels", description: "Add or modify vessels" },
      ],
    },
    {
      id: "port_calls",
      label: "Port calls",
      permissions: [
        { id: "port_call:read", label: "View port calls", description: "See port call list and details" },
        { id: "port_call:write", label: "Create & edit port calls", description: "Add or modify port calls" },
      ],
    },
    {
      id: "da",
      label: "Disbursements (DA)",
      permissions: [
        { id: "da:read", label: "View disbursements", description: "See DA list and details" },
        { id: "da:write", label: "Create & edit DAs", description: "Create Proforma/Final DAs" },
        { id: "da:approve", label: "Approve DAs", description: "Approve DAs before dispatch" },
        { id: "da:send", label: "Send DAs", description: "Dispatch DAs to recipients" },
      ],
    },
    {
      id: "ai",
      label: "AI & parsing",
      permissions: [
        { id: "ai:parse", label: "Run AI parse", description: "Trigger AI parsing on emails" },
      ],
    },
    {
      id: "admin",
      label: "Administration",
      permissions: [
        { id: "admin:users", label: "Manage users", description: "Create, edit, and remove users" },
        { id: "admin:roles", label: "Manage roles", description: "Create and edit roles and permissions" },
      ],
    },
    {
      id: "billing",
      label: "Billing",
      permissions: [
        { id: "billing:manage", label: "Manage billing", description: "View and manage subscription" },
      ],
    },
    {
      id: "settings",
      label: "Settings",
      permissions: [
        { id: "settings:write", label: "Edit settings", description: "Configure tenant settings and integrations" },
      ],
    },
  ],
};

/** Role presets for quick setup. Maps preset id → permission IDs. */
const ROLE_PRESETS = [
  {
    id: "operations_manager",
    label: "Operations Manager",
    description: "Vessels, Port calls, DA (read/write/approve/send), AI parse",
    permissions: [
      "vessel:read",
      "vessel:write",
      "port_call:read",
      "port_call:write",
      "da:read",
      "da:write",
      "da:approve",
      "da:send",
      "ai:parse",
    ],
  },
  {
    id: "finance_only",
    label: "Finance Only",
    description: "DA (read/write/approve/send), Billing",
    permissions: [
      "da:read",
      "da:write",
      "da:approve",
      "da:send",
      "billing:manage",
    ],
  },
  {
    id: "viewer",
    label: "Viewer",
    description: "Vessels (read), Port calls (read), DA (read)",
    permissions: ["vessel:read", "port_call:read", "da:read"],
  },
  {
    id: "admin",
    label: "Admin",
    description: "All permissions",
    permissions: [
      "vessel:read",
      "vessel:write",
      "port_call:read",
      "port_call:write",
      "da:read",
      "da:write",
      "da:approve",
      "da:send",
      "ai:parse",
      "admin:users",
      "admin:roles",
      "billing:manage",
      "settings:write",
    ],
  },
] as const;

export function RoleForm() {
  const { roleId } = useParams();
  const navigate = useNavigate();
  const isEdit = !!roleId;

  const [name, setName] = useState("");
  const [permissions, setPermissions] = useState<string[]>([]);
  const [manifest, setManifest] = useState<PermissionsManifest | null>(null);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadManifest() {
      try {
        const res = await api.get<SingleResponse<PermissionsManifest>>(
          "/admin/permissions",
        );
        setManifest(res.data.data);
      } catch {
        setManifest(FALLBACK_MANIFEST);
      }
    }
    loadManifest();
  }, []);

  useEffect(() => {
    if (!roleId) {
      setLoading(false);
      return;
    }
    async function loadData() {
      try {
        const res = await api.get<SingleResponse<RoleResponse>>(
          `/admin/roles/${roleId}`,
        );
        const r = res.data.data;
        setName(r.name);
        setPermissions(r.permissions);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load role",
        );
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [roleId]);

  function togglePermission(perm: string) {
    setPermissions((prev) =>
      prev.includes(perm) ? prev.filter((p) => p !== perm) : [...prev, perm],
    );
  }

  function toggleModuleAll(module: PermissionModule, select: boolean) {
    const ids = module.permissions.map((p) => p.id);
    setPermissions((prev) => {
      const without = prev.filter((p) => !ids.includes(p));
      return select ? [...without, ...ids] : without;
    });
  }

  function isModuleAllSelected(module: PermissionModule): boolean {
    return module.permissions.every((p) => permissions.includes(p.id));
  }

  function applyPreset(preset: (typeof ROLE_PRESETS)[number]) {
    setPermissions([...preset.permissions]);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (isEdit) {
        const body: RoleUpdate = { name: name.trim(), permissions };
        await api.put(`/admin/roles/${roleId}`, body);
      } else {
        const body: RoleCreate = {
          name: name.trim(),
          permissions,
        };
        await api.post("/admin/roles", body);
      }
      navigate("/admin/roles");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to save role",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading || !manifest) return <LoadingSpinner />;

  const inputClass =
    "w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-500 dark:placeholder:text-slate-400 transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20";

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-800 dark:text-slate-100">
        {isEdit ? "Edit Role" : "New Role"}
      </h1>

      <div className="mx-auto max-w-2xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="name"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setName(e.target.value)
              }
              required
              className={inputClass}
              placeholder="e.g. Operations Manager"
            />
          </div>

          <div>
            <label className="mb-3 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Permissions
            </label>
            {isEdit ? (
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <span className="text-sm text-slate-500 dark:text-slate-400">
                  Reset to template:
                </span>
                <select
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
                    const id = e.target.value;
                    if (id) {
                      const preset = ROLE_PRESETS.find((p) => p.id === id);
                      if (preset) applyPreset(preset);
                      e.target.value = "";
                    }
                  }}
                  className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
                >
                  <option value="">Choose preset…</option>
                  {ROLE_PRESETS.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label}
                    </option>
                  ))}
                </select>
              </div>
            ) : (
              <div className="mb-4">
                <p className="mb-2 text-sm text-slate-500 dark:text-slate-400">
                  Start from template (optional):
                </p>
                <div className="flex flex-wrap gap-2">
                  {ROLE_PRESETS.map((preset) => (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => applyPreset(preset)}
                      className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-left text-sm transition-colors hover:border-mint-500 hover:bg-mint-50/50 dark:border-slate-600 dark:bg-slate-800 dark:hover:border-mint-500 dark:hover:bg-navy-800/50"
                    >
                      <span className="font-medium text-slate-700 dark:text-slate-200">
                        {preset.label}
                      </span>
                      <span className="mt-0.5 block text-xs text-slate-500 dark:text-slate-400">
                        {preset.description}
                      </span>
                    </button>
                  ))}
                </div>
              </div>
            )}
            <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">
              Group permissions by module. Select the access level for each area.
            </p>
            <div className="space-y-4">
              {manifest.modules.map((module) => (
                <Card key={module.id} className="overflow-hidden">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 py-4">
                    <CardTitle className="text-base font-medium">
                      {module.label}
                    </CardTitle>
                    <button
                      type="button"
                      onClick={() =>
                        toggleModuleAll(
                          module,
                          !isModuleAllSelected(module),
                        )
                      }
                      className="text-xs font-medium text-mint-600 hover:text-mint-700 dark:text-mint-400 dark:hover:text-mint-300"
                    >
                      {isModuleAllSelected(module)
                        ? "Deselect all"
                        : "Select all"}
                    </button>
                  </CardHeader>
                  <CardContent className="space-y-3 pt-0">
                    {module.permissions.map((perm) => (
                      <label
                        key={perm.id}
                        className="flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 px-3 py-2.5 transition-colors hover:bg-slate-50 has-[:checked]:border-mint-500 has-[:checked]:bg-mint-50/50 dark:border-slate-600 dark:hover:bg-slate-800 dark:has-[:checked]:border-mint-500 dark:has-[:checked]:bg-navy-800/50"
                      >
                        <input
                          type="checkbox"
                          checked={permissions.includes(perm.id)}
                          onChange={() => togglePermission(perm.id)}
                          className="mt-0.5 h-4 w-4 rounded border-slate-300 text-mint-500 focus:ring-mint-500 dark:border-slate-500"
                        />
                        <span className="flex-1">
                          <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                            {perm.label}
                          </span>
                          {perm.description && (
                            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                              {perm.description}
                            </p>
                          )}
                        </span>
                      </label>
                    ))}
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting
                ? "Saving..."
                : isEdit
                  ? "Update Role"
                  : "Create Role"}
            </button>
            <button
              type="button"
              onClick={() => navigate("/admin/roles")}
              className="rounded-lg border border-slate-300 px-6 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
