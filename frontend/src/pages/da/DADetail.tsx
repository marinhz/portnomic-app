import { useState, useEffect, useCallback } from "react";
import { Link, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type { SingleResponse, DAResponse } from "@/api/types";
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

  useEffect(() => {
    loadDA();
  }, [loadDA]);

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
        to_addresses: to_addresses.length > 0 ? to_addresses : undefined,
      });
      setShowSendDialog(false);
      setTimeout(loadDA, 2000);
    } catch (err) {
      setActionError(
        err instanceof ApiError ? err.message : "Failed to send DA",
      );
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
            {da.pdf_blob_id && (
              <a
                href={`/api/v1/da/${da.id}/pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                View PDF
              </a>
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
              {actionLoading ? "Sending..." : "Confirm Send"}
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
                  Amount
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
              {da.line_items.map((item, idx) => (
                <tr key={idx}>
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
                    {item.currency}{" "}
                    {item.amount.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                    })}
                  </td>
                </tr>
              ))}
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
