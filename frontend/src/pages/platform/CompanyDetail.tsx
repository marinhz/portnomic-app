import { useState, useEffect } from "react";
import { Link, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type { SingleResponse, TenantResponse } from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export function CompanyDetail() {
  const { companyId } = useParams();
  const [tenant, setTenant] = useState<TenantResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!companyId) return;
    api
      .get<SingleResponse<TenantResponse>>(`/platform/tenants/${companyId}`)
      .then((res) => setTenant(res.data.data))
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load company",
        );
      })
      .finally(() => setLoading(false));
  }, [companyId]);

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
    );
  if (!tenant)
    return (
      <div className="rounded-lg bg-amber-50 p-4 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
        Company not found
      </div>
    );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{tenant.name}</h1>
        <Link
          to="/admin/companies"
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Back to Companies
        </Link>
      </div>

      <div className="mx-auto max-w-2xl rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <dl className="space-y-4">
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Name</dt>
            <dd className="mt-1 text-slate-800 dark:text-slate-200">{tenant.name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Slug</dt>
            <dd className="mt-1 font-mono text-slate-800 dark:text-slate-200">{tenant.slug}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Created</dt>
            <dd className="mt-1 text-slate-800 dark:text-slate-200">
              {new Date(tenant.created_at).toLocaleString()}
            </dd>
          </div>
        </dl>

        <p className="mt-6 text-sm text-slate-500 dark:text-slate-400">
          To manage users for this company, log in as a user belonging to this
          tenant and use the Admin → Users section.
        </p>
      </div>
    </div>
  );
}
