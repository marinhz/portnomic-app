import { Link, useLoaderData } from "react-router";
import { SideBySideAudit } from "@/components/sentinel";
import type { PortCallAuditLoaderData } from "./loaders";

/**
 * Sentinel Audit page: Side-by-side Vendor Claims vs Operational Reality vs Variance.
 * Linked from SentinelAlert "View audit details" or Port Call detail.
 */
export function PortCallAudit() {
  const { discrepancies, portCallId, error } =
    useLoaderData() as PortCallAuditLoaderData;

  return (
    <div className="space-y-6">
      <Link
        to={`/port-calls/${portCallId}`}
        className="mb-4 inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
      >
        &larr; Back to Port Call
      </Link>

      <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
        Sentinel Audit
      </h1>
      <p className="text-slate-600 dark:text-slate-400">
        Compare vendor claims (Invoice/DA) against operational reality (SOF, AIS, Noon Report).
        Each discrepancy shows its data sources (Manual PDF or Email) for audit transparency.
      </p>

      {error && (
        <div
          className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300"
          role="alert"
        >
          {error}
        </div>
      )}

      <div className="rounded-lg border border-border bg-card p-6 shadow-sm">
        <SideBySideAudit
          discrepancies={discrepancies}
          portCallId={portCallId}
        />
      </div>
    </div>
  );
}
