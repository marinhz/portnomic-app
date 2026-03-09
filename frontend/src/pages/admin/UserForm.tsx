import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  UserResponse,
  RoleResponse,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export function UserForm() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const isEdit = !!userId;

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState("");
  const [mfaEnabled, setMfaEnabled] = useState(false);

  const [roles, setRoles] = useState<RoleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const rolesRes = await api.get<{ data: RoleResponse[] }>("/admin/roles");
        setRoles(rolesRes.data.data);

        if (userId) {
          const userRes = await api.get<SingleResponse<UserResponse>>(
            `/admin/users/${userId}`,
          );
          const u = userRes.data.data;
          setEmail(u.email);
          setRoleId(u.role_id);
          setMfaEnabled(u.mfa_enabled);
        }
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load data",
        );
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [userId]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      if (isEdit) {
        await api.put(`/admin/users/${userId}`, {
          email,
          role_id: roleId,
          mfa_enabled: mfaEnabled,
        });
      } else {
        await api.post("/admin/users", {
          email,
          password,
          role_id: roleId,
          mfa_enabled: mfaEnabled,
        });
      }
      navigate("/admin/users");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to save user",
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
        {isEdit ? "Edit User" : "New User"}
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
              htmlFor="email"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setEmail(e.target.value)
              }
              required
              className={inputClass}
              placeholder="user@company.com"
            />
          </div>

          {!isEdit && (
            <div>
              <label
                htmlFor="password"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setPassword(e.target.value)
                }
                required
                minLength={8}
                className={inputClass}
                placeholder="Minimum 8 characters"
              />
            </div>
          )}

          <div>
            <label
              htmlFor="role"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Role
            </label>
            <select
              id="role"
              value={roleId}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setRoleId(e.target.value)
              }
              required
              className={inputClass}
            >
              <option value="">Select role...</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            <input
              id="mfa"
              type="checkbox"
              checked={mfaEnabled}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setMfaEnabled(e.target.checked)
              }
              className="h-4 w-4 rounded border-slate-300 text-mint-500 focus:ring-mint-500 dark:border-slate-500"
            />
            <label htmlFor="mfa" className="text-sm font-medium text-slate-700 dark:text-slate-300">
              Enable MFA
            </label>
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
                  ? "Update User"
                  : "Create User"}
            </button>
            <button
              type="button"
              onClick={() => navigate("/admin/users")}
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
