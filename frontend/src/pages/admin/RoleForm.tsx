import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  RoleResponse,
  RoleCreate,
  RoleUpdate,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";

const KNOWN_PERMISSIONS = [
  "vessel:read",
  "vessel:write",
  "port_call:read",
  "port_call:write",
  "admin:users",
  "admin:roles",
  "billing:manage",
  "settings:write",
  "ai:parse",
  "da:read",
  "da:write",
  "da:approve",
  "da:send",
];

export function RoleForm() {
  const { roleId } = useParams();
  const navigate = useNavigate();
  const isEdit = !!roleId;

  const [name, setName] = useState("");
  const [permissions, setPermissions] = useState<string[]>([]);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

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

  if (loading) return <LoadingSpinner />;

  const inputClass =
    "w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

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

        <form onSubmit={handleSubmit} className="space-y-4">
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
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Permissions
            </label>
            <div className="flex flex-wrap gap-3">
              {KNOWN_PERMISSIONS.map((perm) => (
                <label
                  key={perm}
                  className="flex cursor-pointer items-center gap-2 rounded-lg border border-slate-200 px-3 py-2 transition-colors hover:bg-slate-50 has-[:checked]:border-mint-500 has-[:checked]:bg-mint-100 dark:border-slate-600 dark:hover:bg-slate-800 dark:has-[:checked]:border-mint-500 dark:has-[:checked]:bg-navy-800"
                >
                  <input
                    type="checkbox"
                    checked={permissions.includes(perm)}
                    onChange={() => togglePermission(perm)}
                    className="h-4 w-4 rounded border-slate-300 text-mint-500 focus:ring-mint-500 dark:border-slate-500"
                  />
                  <span className="text-sm text-slate-700 dark:text-slate-200">{perm}</span>
                </label>
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
