import { useState, useEffect } from "react";
import { Link, useSearchParams } from "react-router";
import { AlertTriangle } from "lucide-react";
import api, { ApiError } from "@/api/client";
import type { PaginatedResponse, DAListResponse } from "@/api/types";
import { useAuth } from "@/auth/AuthContext";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Pagination } from "@/components/Pagination";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  pending_approval: "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300",
  approved: "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
  sent: "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
};

const STATUS_LABELS: Record<string, string> = {
  draft: "Draft",
  pending_approval: "Pending Approval",
  approved: "Approved",
  sent: "Sent",
};

export function DAList() {
  const { user } = useAuth();
  const [searchParams, setSearchParams] = useSearchParams();
  const [das, setDAs] = useState<DAListResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const page = Number(searchParams.get("page") ?? "1");
  const statusFilter = searchParams.get("status") ?? "";
  const hasLeakageFilter = searchParams.get("has_anomalies") === "true";

  const leakageDetectorEnabled =
    user?.leakage_detector_enabled ?? user?.is_platform_admin ?? false;
  const hasDARead = user?.permissions?.includes("da:read") ?? false;
  const showLeakageUI = leakageDetectorEnabled && hasDARead;

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string | number | boolean> = {
      page,
      per_page: 20,
    };
    if (statusFilter) params.da_status = statusFilter;
    if (hasLeakageFilter) params.has_anomalies = true;

    api
      .get<PaginatedResponse<DAListResponse>>("/da", { params })
      .then((res) => {
        setDAs(res.data.data);
        setTotal(res.data.meta.total);
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load DAs");
      })
      .finally(() => setLoading(false));
  }, [page, statusFilter, hasLeakageFilter]);

  function handleStatusFilter(status: string) {
    const params = new URLSearchParams(searchParams);
    if (status) {
      params.set("status", status);
    } else {
      params.delete("status");
    }
    params.set("page", "1");
    setSearchParams(params);
  }

  function handleLeakageFilter(active: boolean) {
    const params = new URLSearchParams(searchParams);
    if (active) {
      params.set("has_anomalies", "true");
    } else {
      params.delete("has_anomalies");
    }
    params.set("page", "1");
    setSearchParams(params);
  }

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
    );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
          Disbursement Accounts
        </h1>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        {["", "draft", "pending_approval", "approved", "sent"].map((s) => (
          <button
            key={s}
            onClick={() => handleStatusFilter(s)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              statusFilter === s
                ? "bg-primary text-primary-foreground"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            }`}
          >
            {s ? STATUS_LABELS[s] ?? s : "All"}
          </button>
        ))}
        {showLeakageUI && (
          <button
            onClick={() => handleLeakageFilter(!hasLeakageFilter)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
              hasLeakageFilter
                ? "bg-primary text-primary-foreground"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-slate-600"
            }`}
          >
            Has Leakage
          </button>
        )}
      </div>

      {das.length === 0 ? (
        <div className="rounded-lg border border-slate-200 bg-white p-8 text-center dark:border-slate-700 dark:bg-slate-900">
          <p className="text-slate-500 dark:text-slate-400">
            {hasLeakageFilter
              ? "No DAs with Leakage Detector findings."
              : "No disbursement accounts found."}
          </p>
          <p className="mt-2 text-sm text-slate-400 dark:text-slate-500">
            {hasLeakageFilter
              ? "Try removing the Has Leakage filter to see all DAs."
              : "Generate a DA from a port call to get started."}
          </p>
        </div>
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
                  {showLeakageUI && (
                    <th className="w-10 px-4 py-3 text-center text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                      <span className="sr-only">Leakage</span>
                    </th>
                  )}
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Version
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Currency
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Approved
                  </th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                {das.map((da) => (
                  <tr
                    key={da.id}
                    className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50"
                  >
                    {showLeakageUI && (
                      <td className="px-4 py-3 text-center">
                        {da.has_anomalies ? (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <span className="inline-flex items-center justify-center">
                                <AlertTriangle
                                  className="size-4 text-amber-600 dark:text-amber-400"
                                  aria-hidden
                                />
                              </span>
                            </TooltipTrigger>
                            <TooltipContent side="top">
                              Has Leakage Detector findings
                            </TooltipContent>
                          </Tooltip>
                        ) : (
                          <span className="inline-block size-4" aria-hidden />
                        )}
                      </td>
                    )}
                    <td className="px-4 py-3 text-sm font-medium capitalize text-slate-800 dark:text-slate-200">
                      {da.type}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">
                      v{da.version}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          STATUS_COLORS[da.status] ??
                          "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                        }`}
                      >
                        {STATUS_LABELS[da.status] ?? da.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">
                      {da.currency}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                      {new Date(da.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                      {da.approved_at
                        ? new Date(da.approved_at).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link
                        to={`/da/${da.id}`}
                        className="text-sm font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-4">
            <Pagination
              currentPage={page}
              totalPages={Math.ceil(total / 20)}
              onPageChange={(p) => {
                const params = new URLSearchParams(searchParams);
                params.set("page", String(p));
                setSearchParams(params);
              }}
            />
          </div>
        </>
      )}
    </div>
  );
}
