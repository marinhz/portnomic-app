import { useState, useEffect } from "react";
import { Link, useLoaderData, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  PortCallResponse,
  DAListResponse,
} from "@/api/types";
import type { PortCallDetailLoaderData } from "./loaders";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Badge } from "@/components/ui/badge";
import { SentinelAlert } from "@/components/sentinel";
import { useAuth } from "@/auth/AuthContext";

const DA_STATUS_COLORS: Record<string, string> = {
  draft: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  pending_approval: "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300",
  approved: "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
  sent: "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
};

export function PortCallDetail() {
  const { portCallId } = useParams();
  const { user } = useAuth();
  const { portCall, discrepancies, discrepanciesError } =
    useLoaderData() as PortCallDetailLoaderData;
  const [das, setDAs] = useState<DAListResponse[]>([]);
  const [discrepanciesDismissed, setDiscrepanciesDismissed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hasDARead = user?.permissions.includes("da:read") ?? false;
  const hasDAWrite = user?.permissions.includes("da:write") ?? false;

  useEffect(() => {
    if (!portCallId || !hasDARead) {
      setLoading(false);
      return;
    }
    api
      .get<PaginatedResponse<DAListResponse>>("/da", {
        params: { port_call_id: portCallId, per_page: 50 },
      })
      .then((res) => setDAs(res.data.data))
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load DAs"
        );
      })
      .finally(() => setLoading(false));
  }, [portCallId, hasDARead]);

  const statusColorMap: Record<string, string> = {
    planned: "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
    arrived: "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
    berthed: "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300",
    departed: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
    cancelled: "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300",
  };
  const statusColor =
    statusColorMap[portCall.status.toLowerCase()] ??
    "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200";

  const showSentinelAlert =
    !discrepanciesDismissed && discrepancies.length > 0;

  return (
    <div>
      <div
        className="min-h-0"
        aria-live="polite"
        aria-label={showSentinelAlert ? "Sentinel alerts section" : undefined}
      >
        {showSentinelAlert && (
          <div className="mb-6">
            <SentinelAlert
              discrepancies={discrepancies}
              portCallId={portCallId!}
              onDismiss={() => setDiscrepanciesDismissed(true)}
            />
          </div>
        )}
        {discrepanciesError && (
          <div
            className="mb-6 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800 dark:border-amber-800 dark:bg-amber-950/30 dark:text-amber-200"
            role="status"
          >
            Sentinel alerts unavailable: {discrepanciesError}
          </div>
        )}
      </div>

      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link
            to="/port-calls"
            className="mb-2 inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          >
            &larr; Back to Port Calls
          </Link>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            Port Call Details
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to={`/port-calls/${portCallId}/documents`}
            className="text-sm font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          >
            Upload Documents
          </Link>
          <Link
            to={`/port-calls/${portCallId}/audit`}
            className="text-sm font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          >
            Sentinel Audit
          </Link>
          <Link
            to={`/port-calls/${portCallId}/edit`}
            className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Edit Port Call
          </Link>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
          Port Call Details
        </h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Vessel</dt>
            <dd className="mt-1 text-sm">
              <Link
                to={`/vessels/${portCall.vessel_id}`}
                className="font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
              >
                View Vessel
              </Link>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Port ID</dt>
            <dd className="mt-1 text-sm text-slate-800 dark:text-slate-200">{portCall.port_id}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Status</dt>
            <dd className="mt-1">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColor}`}
              >
                {portCall.status}
              </span>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Sync</dt>
            <dd className="mt-1">
              <Badge variant={portCall.source === "ai" ? "info" : "secondary"}>
                {portCall.source === "ai" ? "Auto-generated" : "Manual"}
              </Badge>
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">ETA</dt>
            <dd className="mt-1 text-sm text-slate-800 dark:text-slate-200">
              {portCall.eta ? new Date(portCall.eta).toLocaleString() : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">ETD</dt>
            <dd className="mt-1 text-sm text-slate-800 dark:text-slate-200">
              {portCall.etd ? new Date(portCall.etd).toLocaleString() : "—"}
            </dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Created</dt>
            <dd className="mt-1 text-sm text-slate-800 dark:text-slate-200">
              {new Date(portCall.created_at).toLocaleString()}
            </dd>
          </div>
        </dl>
      </div>

      {hasDARead && (
        <div className="mt-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">
              Disbursement Accounts
            </h2>
            {hasDAWrite && (
              <div className="flex gap-3">
                <Link
                  to={`/da/generate?port_call_id=${portCallId}`}
                  className="rounded-lg bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                >
                  Generate Proforma
                </Link>
                <Link
                  to={`/da/generate?port_call_id=${portCallId}`}
                  className="rounded-lg border border-mint-500 px-3 py-1.5 text-sm font-medium text-navy-800 transition-colors hover:bg-mint-100 dark:border-mint-400 dark:text-mint-100 dark:hover:bg-mint-500/20"
                >
                  Generate Final
                </Link>
              </div>
            )}
          </div>
          {loading ? (
            <LoadingSpinner />
          ) : error ? (
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          ) : das.length === 0 ? (
            <p className="text-sm text-slate-500 dark:text-slate-400">
              No disbursement accounts for this port call.
            </p>
          ) : (
            <div className="space-y-2">
              {das.map((da) => (
                <Link
                  key={da.id}
                  to={`/da/${da.id}`}
                  className="flex items-center justify-between rounded-lg border border-slate-100 p-3 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800/50"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium capitalize text-slate-800 dark:text-slate-200">
                      {da.type}
                    </span>
                    <span className="text-xs text-slate-500 dark:text-slate-400">v{da.version}</span>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${DA_STATUS_COLORS[da.status] ?? "bg-slate-100 text-slate-700"}`}
                    >
                      {da.status.replace("_", " ")}
                    </span>
                  </div>
                  <span className="text-sm text-slate-500 dark:text-slate-400">
                    {new Date(da.created_at).toLocaleDateString()}
                  </span>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
