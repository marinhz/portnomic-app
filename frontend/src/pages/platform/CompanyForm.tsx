import { useState } from "react";
import { useNavigate } from "react-router";
import api, { ApiError } from "@/api/client";
import type { TenantCreate } from "@/api/types";

function slugFromName(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

export function CompanyForm() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [initialAdminEmail, setInitialAdminEmail] = useState("");
  const [initialAdminPassword, setInitialAdminPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleNameChange(value: string) {
    setName(value);
    if (!slug || slug === slugFromName(name)) {
      setSlug(slugFromName(value));
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const body: TenantCreate = {
      name: name.trim(),
      slug: slug.trim().toLowerCase() || slugFromName(name),
    };
    if (initialAdminEmail.trim()) {
      body.initial_admin_email = initialAdminEmail.trim();
      if (initialAdminPassword) {
        body.initial_admin_password = initialAdminPassword;
      }
    }

    try {
      await api.post("/platform/tenants", body);
      navigate("/admin/companies");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to create company",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-500 dark:placeholder:text-slate-400 transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20";

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-800 dark:text-slate-100">
        Add Company
      </h1>

      <div className="mx-auto max-w-2xl rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/30 p-3 text-sm text-red-700 dark:text-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="name"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Company Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => handleNameChange(e.target.value)}
              required
              className={inputClass}
              placeholder="Acme Shipping"
            />
          </div>

          <div>
            <label
              htmlFor="slug"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Slug (URL-safe identifier)
            </label>
            <input
              id="slug"
              type="text"
              value={slug}
              onChange={(e) => setSlug(e.target.value.toLowerCase())}
              required
              className={inputClass}
              placeholder="acme-shipping"
            />
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Lowercase, hyphens only. Used for inbound email routing.
            </p>
          </div>

          <div className="border-t border-slate-200 dark:border-slate-700 pt-4">
            <p className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
              Optional: Create first admin user
            </p>
            <div className="space-y-4">
              <div>
                <label
                  htmlFor="initial_admin_email"
                  className="mb-1 block text-sm text-slate-600 dark:text-slate-400"
                >
                  Admin Email
                </label>
                <input
                  id="initial_admin_email"
                  type="email"
                  value={initialAdminEmail}
                  onChange={(e) => setInitialAdminEmail(e.target.value)}
                  className={inputClass}
                  placeholder="admin@acme.com"
                />
              </div>
              <div>
                <label
                  htmlFor="initial_admin_password"
                  className="mb-1 block text-sm text-slate-600 dark:text-slate-400"
                >
                  Admin Password
                </label>
                <input
                  id="initial_admin_password"
                  type="password"
                  value={initialAdminPassword}
                  onChange={(e) => setInitialAdminPassword(e.target.value)}
                  minLength={8}
                  className={inputClass}
                  placeholder="Minimum 8 characters"
                />
              </div>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? "Creating..." : "Create Company"}
            </button>
            <button
              type="button"
              onClick={() => navigate("/admin/companies")}
              className="rounded-lg border border-slate-300 dark:border-slate-600 px-6 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
