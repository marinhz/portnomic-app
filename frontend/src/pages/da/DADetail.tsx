import React, { useState, useEffect, useCallback } from "react";
import { Link, useParams } from "react-router";
import { AlertTriangle, ChevronUp, Download } from "lucide-react";
import { toast } from "sonner";
import api, { ApiError } from "@/api/client";
import { useHighRiskToast } from "@/hooks/useHighRiskToast";
import type {
  SingleResponse,
  DAResponse,
  DALineItem,
  DAAnomalyResponse,
  PaginatedResponse,
} from "@/api/types";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { useAuth } from "@/auth/AuthContext";

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

const SEVERITY_BADGE: Record<string, "destructive" | "warning" | "info" | "secondary"> = {
  critical: "destructive",
  high: "destructive",
  medium: "warning",
  low: "info",
};

const EVIDENCE_LABELS: Record<string, string> = {
  invoice_date: "Invoice date",
  eta: "Vessel ETA",
  etd: "Vessel ETD",
  service_time: "Service time",
  rate_type: "Rate type",
  duplicate_ref: "Duplicate reference",
  amount: "Amount",
  invoiced_grt: "Invoiced GRT",
  noon_report_grt: "Noon report GRT",
  rate: "Rate",
  tariff_rate: "Tariff rate",
  invoiced: "Invoiced",
};

function formatEvidenceValue(value: unknown): string {
  if (value == null) return "—";
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}/.test(value)) {
    try {
      const d = new Date(value);
      return d.toLocaleString(undefined, {
        dateStyle: "medium",
        timeStyle: "short",
        timeZone: "UTC",
      });
    } catch {
      return String(value);
    }
  }
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 4 });
  return String(value);
}

function AnomalyEvidence({ evidence }: { evidence: Record<string, unknown> }) {
  const entries = Object.entries(evidence).filter(([, v]) => v != null && v !== "");
  if (entries.length === 0) return null;
  return (
    <dl className="mt-2 space-y-1 rounded border border-slate-200 bg-white p-3 text-xs dark:border-slate-600 dark:bg-slate-900">
      {entries.map(([key, value]) => (
        <div key={key} className="flex gap-2">
          <dt className="shrink-0 font-medium text-slate-500 dark:text-slate-400">
            {EVIDENCE_LABELS[key] ?? key.replace(/_/g, " ")}:
          </dt>
          <dd className="text-slate-700 dark:text-slate-300">{formatEvidenceValue(value)}</dd>
        </div>
      ))}
    </dl>
  );
}

/** Match anomaly to line item by description / line_item_ref */
function anomaliesForLineItem(
  item: DALineItem,
  anomalies: DAAnomalyResponse[],
): DAAnomalyResponse[] {
  const desc = (item.description || "").trim().toLowerCase();
  return anomalies.filter((a) => {
    const ref = (a.line_item_ref || "").trim().toLowerCase();
    if (!ref) return false;
    return desc.includes(ref) || ref.includes(desc) || desc === ref;
  });
}

export function DADetail() {
  const { daId } = useParams();
  const { user } = useAuth();
  const [da, setDA] = useState<DAResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [sendEmails, setSendEmails] = useState("");
  const [showSendDialog, setShowSendDialog] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [anomalies, setAnomalies] = useState<DAAnomalyResponse[]>([]);
  const [expandedAnomalyId, setExpandedAnomalyId] = useState<string | null>(null);

  const loadDA = useCallback(() => {
    if (!daId) return;
    api
      .get<SingleResponse<DAResponse>>(`/da/${daId}`)
      .then((res) => setDA(res.data.data))
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load DA",
        );
      })
      .finally(() => setLoading(false));
  }, [daId]);

  const loadAnomalies = useCallback(() => {
    if (!daId) return;
    api
      .get<PaginatedResponse<DAAnomalyResponse>>(`/da/${daId}/anomalies`)
      .then((res) => setAnomalies(res.data.data ?? []))
      .catch((err) => {
        console.warn("[Leakage Detector] Failed to load anomalies:", err?.response?.status, err?.response?.data);
        setAnomalies([]);
      });
  }, [daId]);

  useEffect(() => {
    loadDA();
  }, [loadDA]);

  useEffect(() => {
    if (daId && !loading && !error) {
      loadAnomalies();
    }
  }, [daId, loading, error, loadAnomalies]);

  useHighRiskToast({
    anomalies,
    entityId: daId ?? undefined,
    target: "da",
  });

  const canApprove =
    da &&
    (da.status === "draft" || da.status === "pending_approval") &&
    user?.permissions.includes("da:approve");

  const canSend =
    da &&
    da.status === "approved" &&
    user?.permissions.includes("da:send");

  async function handleApprove() {
    if (!daId) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const res = await api.post<SingleResponse<DAResponse>>(
        `/da/${daId}/approve`,
      );
      setDA(res.data.data);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Failed to approve DA",
      );
    } finally {
      setActionLoading(false);
    }
  }

  async function handleDownloadPdf() {
    if (!daId) return;
    setPdfLoading(true);
    try {
      const res = await api.get(`/da/${daId}/pdf`, {
        responseType: "blob",
      });
      const blob = res.data as Blob;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `DA_${daId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("PDF downloaded");
      loadDA();
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Failed to download PDF";
      toast.error(msg);
    } finally {
      setPdfLoading(false);
    }
  }

  async function handleSend() {
    if (!daId) return;
    setActionLoading(true);
    setActionError(null);
    try {
      const to_addresses = sendEmails
        .split(",")
        .map((e) => e.trim())
        .filter(Boolean);
      await api.post(`/da/${daId}/send`, {
        to_addresses,
      });
      setShowSendDialog(false);
      const toastId = toast.loading("Generating PDF…");
      const maxAttempts = 40;
      const intervalMs = 2000;
      for (let i = 0; i < maxAttempts; i++) {
        await new Promise((r) => setTimeout(r, intervalMs));
        const res = await api.get<SingleResponse<DAResponse>>(`/da/${daId}`);
        const updated = res.data.data;
        if (updated.pdf_blob_id || updated.status === "sent") {
          setDA(updated);
          toast.success("PDF ready. View PDF button is now available.", {
            id: toastId,
          });
          return;
        }
      }
      toast.warning(
        "PDF is still processing. Refresh the page in a moment—the View PDF button will appear when ready.",
        { id: toastId, duration: 8000 },
      );
      loadDA();
    } catch (err) {
      const msg =
        err instanceof ApiError ? err.message : "Failed to send DA";
      setActionError(msg);
      toast.error(msg);
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
    );
  if (!da) return null;

  return (
    <div>
      <div className="mb-6">
        <Link
          to="/da"
          className="mb-2 inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
        >
          &larr; Back to Disbursement Accounts
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              {da.type.charAt(0).toUpperCase() + da.type.slice(1)} DA
              <span className="ml-2 text-lg font-normal text-slate-500 dark:text-slate-400">
                v{da.version}
              </span>
            </h1>
            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
              {da.id.slice(0, 8)} &middot; Created{" "}
              {new Date(da.created_at).toLocaleString()}
            </p>
          </div>
          <div className="flex gap-3">
            {(da.status === "approved" || da.status === "sent") && (
              <button
                type="button"
                onClick={handleDownloadPdf}
                disabled={pdfLoading}
                className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                <Download className="size-4" />
                {pdfLoading ? "Generating…" : "Download PDF"}
              </button>
            )}
            {canApprove && (
              <button
                onClick={handleApprove}
                disabled={actionLoading}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
              >
                {actionLoading ? "Approving..." : "Approve"}
              </button>
            )}
            {canSend && (
              <button
                onClick={() => setShowSendDialog(true)}
                disabled={actionLoading}
                className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-green-700 disabled:opacity-50"
              >
                Send
              </button>
            )}
          </div>
        </div>
      </div>

      {actionError && (
        <div className="mb-4 rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/50 dark:text-red-300">
          {actionError}
        </div>
      )}

      {showSendDialog && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-950/50">
          <h3 className="mb-2 font-medium text-green-800 dark:text-green-300">
            Send Disbursement Account
          </h3>
          <p className="mb-3 text-sm text-green-700 dark:text-green-400">
            Enter recipient email addresses (comma-separated), or leave empty to
            skip email and just generate PDF.
          </p>
          <input
            type="text"
            value={sendEmails}
            onChange={(e) => setSendEmails(e.target.value)}
            placeholder="recipient@example.com, another@example.com"
            className="mb-3 w-full rounded-lg border border-green-300 px-3 py-2 text-sm focus:border-green-500 focus:ring-1 focus:ring-green-500 focus:outline-none dark:border-green-700 dark:bg-slate-900 dark:text-slate-100"
          />
          <div className="flex gap-3">
            <button
              onClick={handleSend}
              disabled={actionLoading}
              className="rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
            >
              {actionLoading ? "Generating PDF…" : "Confirm Send"}
            </button>
            <button
              onClick={() => setShowSendDialog(false)}
              className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Status
          </p>
          <p className="mt-2">
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[da.status] ?? "bg-slate-100 text-slate-700"}`}
            >
              {STATUS_LABELS[da.status] ?? da.status}
            </span>
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Total
          </p>
          <p className="mt-2 text-xl font-bold text-navy-800 dark:text-mint-300">
            {da.currency} {da.totals.total.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Approved
          </p>
          <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
            {da.approved_at
              ? new Date(da.approved_at).toLocaleString()
              : "Not yet"}
          </p>
        </div>
        <div className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Sent
          </p>
          <p className="mt-2 text-sm text-slate-700 dark:text-slate-200">
            {da.sent_at ? new Date(da.sent_at).toLocaleString() : "Not yet"}
          </p>
        </div>
      </div>

      {anomalies.length > 0 && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle className="size-4" />
          <AlertTitle>Audit discrepancies detected</AlertTitle>
          <AlertDescription>
            {anomalies.length} anomaly(ies) found. Review flagged line items below for invoiced vs.
            expected values.
          </AlertDescription>
        </Alert>
      )}

      <div className="rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="border-b border-slate-200 px-6 py-4 dark:border-slate-700">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Line Items</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
                <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Description
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Qty
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  Unit Price
                </th>
                <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                  {anomalies.length > 0 ? "Invoiced / Expected" : "Amount"}
                </th>
                {anomalies.length > 0 && (
                  <th className="w-24 px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
                    Audit
                  </th>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {da.line_items.map((item, idx) => {
                const itemAnomalies = anomaliesForLineItem(item, anomalies);
                const hasAnomaly = itemAnomalies.length > 0;
                const maxSeverity =
                  itemAnomalies.length > 0
                    ? itemAnomalies.reduce((a, b) =>
                        ["critical", "high", "medium", "low"].indexOf(a.severity) <=
                        ["critical", "high", "medium", "low"].indexOf(b.severity)
                          ? a
                          : b,
                      )
                    : null;
                const primaryAnomaly = itemAnomalies[0];
                const invoicedVal =
                  primaryAnomaly?.invoiced_value ?? item.amount;
                const expectedVal = primaryAnomaly?.expected_value;

                return (
                  <React.Fragment key={idx}>
                    <tr
                      className={
                        hasAnomaly
                          ? "bg-amber-50/50 dark:bg-amber-950/20"
                          : undefined
                      }
                    >
                      <td className="px-6 py-3 text-sm text-slate-800 dark:text-slate-200">
                        {item.description}
                      </td>
                      <td className="px-6 py-3 text-right text-sm text-slate-600 dark:text-slate-300">
                        {item.quantity}
                      </td>
                      <td className="px-6 py-3 text-right text-sm text-slate-600 dark:text-slate-300">
                        {item.unit_price.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                      <td className="px-6 py-3 text-right text-sm font-medium text-slate-800 dark:text-slate-200">
                        {expectedVal != null ? (
                          <span className="flex flex-col items-end gap-0.5">
                            <span className="text-amber-700 dark:text-amber-400">
                              {item.currency}{" "}
                              {Number(invoicedVal).toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                              })}{" "}
                              (invoiced)
                            </span>
                            <span className="text-green-700 dark:text-green-400">
                              {item.currency}{" "}
                              {Number(expectedVal).toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                              })}{" "}
                              (expected)
                            </span>
                          </span>
                        ) : (
                          <>
                            {item.currency}{" "}
                            {item.amount.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                            })}
                          </>
                        )}
                      </td>
                      {anomalies.length > 0 && (
                        <td className="px-6 py-3">
                          {hasAnomaly && maxSeverity ? (
                            <div className="flex flex-wrap items-center gap-1">
                              {itemAnomalies.map((a) => (
                                <Badge
                                  key={a.id}
                                  variant={
                                    SEVERITY_BADGE[a.severity] ?? "secondary"
                                  }
                                  className="cursor-pointer gap-1"
                                  onClick={() =>
                                    setExpandedAnomalyId(
                                      expandedAnomalyId === a.id ? null : a.id,
                                    )
                                  }
                                >
                                  <AlertTriangle className="size-3" />
                                  {a.rule_id}
                                </Badge>
                              ))}
                            </div>
                          ) : (
                            <span className="text-slate-400">—</span>
                          )}
                        </td>
                      )}
                    </tr>
                    {itemAnomalies.map((a) =>
                      expandedAnomalyId === a.id ? (
                          <tr key={`exp-${a.id}`}>
                            <td
                              colSpan={anomalies.length > 0 ? 5 : 4}
                              className="bg-slate-50 px-6 py-4 dark:bg-slate-800/50"
                            >
                              <div className="space-y-2 text-sm">
                                <p className="font-medium text-slate-800 dark:text-slate-200">
                                  {a.rule_id} — {a.description}
                                </p>
                                {a.raw_evidence &&
                                  Object.keys(a.raw_evidence).length > 0 && (
                                    <AnomalyEvidence evidence={a.raw_evidence} />
                                  )}
                                <button
                                  type="button"
                                  onClick={() => setExpandedAnomalyId(null)}
                                  className="flex items-center gap-1 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                                >
                                  <ChevronUp className="size-4" />
                                  Collapse
                                </button>
                              </div>
                            </td>
                          </tr>
                        ) : null,
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
            <tfoot>
              <tr className="border-t border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
                <td
                  colSpan={3}
                  className="px-6 py-3 text-right text-sm font-medium text-slate-600 dark:text-slate-300"
                >
                  Subtotal
                </td>
                <td className="px-6 py-3 text-right text-sm font-medium text-slate-800 dark:text-slate-200">
                  {da.currency}{" "}
                  {da.totals.subtotal.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                  })}
                </td>
              </tr>
              {da.totals.tax > 0 && (
                <tr className="bg-slate-50 dark:bg-slate-800/80">
                  <td
                    colSpan={3}
                    className="px-6 py-3 text-right text-sm font-medium text-slate-600 dark:text-slate-300"
                  >
                    Tax
                  </td>
                  <td className="px-6 py-3 text-right text-sm font-medium text-slate-800 dark:text-slate-200">
                    {da.currency}{" "}
                    {da.totals.tax.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                </tr>
              )}
              <tr className="bg-mint-100 dark:bg-navy-800">
                <td
                  colSpan={3}
                  className="px-6 py-3 text-right text-sm font-bold text-navy-800 dark:text-mint-200"
                >
                  Total
                </td>
                <td className="px-6 py-3 text-right text-sm font-bold text-navy-800 dark:text-mint-200">
                  {da.currency}{" "}
                  {da.totals.total.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                  })}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}
