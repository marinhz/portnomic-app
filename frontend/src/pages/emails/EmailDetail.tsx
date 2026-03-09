import { useState, useEffect, useCallback, useRef } from "react";
import { useParams, Link, useNavigate } from "react-router";
import api, { ApiError } from "@/api/client";
import { dispatchEmissionReportCreated } from "@/events/emissions";
import { useAuth } from "@/auth/AuthContext";
import type {
  SingleResponse,
  EmailResponse,
  ParseJobResponse,
  ParsedEmailResult,
  EmissionReportDetailResponse,
  EmissionExtraction,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Badge } from "@/components/ui/badge";

function StatusBadge({ status }: { status: string }) {
  const variant =
    status === "completed"
      ? "success"
      : status === "failed" || status === "invalid"
        ? "destructive"
        : status === "processing"
          ? "info"
          : status === "pending"
            ? "warning"
            : "outline";
  return <Badge variant={variant}>{status}</Badge>;
}

export function EmailDetail() {
  const { emailId } = useParams<{ emailId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [email, setEmail] = useState<EmailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [parseJob, setParseJob] = useState<ParseJobResponse | null>(null);
  const [parsing, setParsing] = useState(false);
  const [polling, setPolling] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [emissionReport, setEmissionReport] =
    useState<EmissionReportDetailResponse | null>(null);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const hasAdminUsers = user?.permissions.includes("admin:users") ?? false;

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (pollTimeoutRef.current) clearTimeout(pollTimeoutRef.current);
    };
  }, []);

  useEffect(() => {
    api
      .get<SingleResponse<EmailResponse>>(`/emails/${emailId}`)
      .then((res) => setEmail(res.data.data))
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load email");
      })
      .finally(() => setLoading(false));
  }, [emailId]);

  const resolvedEmissionReportId =
    parseJob?.result &&
    typeof parseJob.result === "object" &&
    "emission_report_id" in parseJob.result
      ? (parseJob.result as { emission_report_id: string }).emission_report_id
      : email?.emission_report_id ?? undefined;

  useEffect(() => {
    if (!resolvedEmissionReportId || !mountedRef.current) return;
    api
      .get<SingleResponse<EmissionReportDetailResponse>>(
        `/emissions/reports/${resolvedEmissionReportId}`,
      )
      .then((res) => {
        if (mountedRef.current) setEmissionReport(res.data.data);
      })
      .catch(() => {
        if (mountedRef.current) setEmissionReport(null);
      });
  }, [resolvedEmissionReportId]);

  useEffect(() => {
    if (!email) setEmissionReport(null);
  }, [email?.id]);

  const pollJob = useCallback(
    async (jobId: string) => {
      if (!mountedRef.current) return;
      setPolling(true);

      const poll = async () => {
        if (!mountedRef.current) return;
        try {
          const res = await api.get<SingleResponse<ParseJobResponse>>(
            `/ai/parse/${jobId}`,
          );
          const job = res.data.data;
          if (!mountedRef.current) return;
          setParseJob(job);

          if (job.status === "completed" || job.status === "failed") {
            setPolling(false);
            const emissionReportId =
              job.result &&
              typeof job.result === "object" &&
              "emission_report_id" in job.result
                ? (job.result as { emission_report_id: string })
                    .emission_report_id
                : undefined;
            if (emissionReportId) {
              dispatchEmissionReportCreated(emissionReportId);
            }
            if (import.meta.env?.DEV) {
              console.debug("[EmailDetail] Parse job completed", {
                jobId,
                status: job.status,
                emailId,
                emissionReportId,
              });
            }
            try {
              const emailRes = await api.get<SingleResponse<EmailResponse>>(
                `/emails/${emailId}`,
              );
              if (mountedRef.current) setEmail(emailRes.data.data);
            } catch (refetchErr) {
              if (mountedRef.current) {
                setError(
                  refetchErr instanceof ApiError
                    ? refetchErr.message
                    : "Failed to refresh email after parse",
                );
              }
            }
            return;
          }

          pollTimeoutRef.current = setTimeout(poll, 2000);
        } catch (err) {
          if (mountedRef.current) {
            setPolling(false);
            setError(err instanceof ApiError ? err.message : "Failed to poll parse status");
          }
        }
      };

      // Delay first poll to avoid race with backend commit
      pollTimeoutRef.current = setTimeout(poll, 400);
    },
    [emailId],
  );

  const handleParse = async () => {
    if (!emailId || !email) return;
    setParsing(true);
    setError(null);
    try {
      const res = await api.post<SingleResponse<ParseJobResponse>>("/ai/parse", {
        email_id: emailId,
      });
      const job = res.data.data;
      setParseJob(job);
      setEmail((prev) =>
        prev ? { ...prev, processing_status: "pending" } : prev,
      );
      pollJob(job.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to start parse");
    } finally {
      setParsing(false);
    }
  };

  const handleMarkInvalid = async () => {
    if (!emailId) return;
    try {
      await api.put(`/ai/emails/${emailId}/status`, {
        processing_status: "invalid",
        error_reason: "Manually marked as invalid by operator",
      });
      const res = await api.get<SingleResponse<EmailResponse>>(
        `/emails/${emailId}`,
      );
      setEmail(res.data.data);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to update status",
      );
    }
  };

  const handleDelete = async () => {
    if (!emailId) return;
    setDeleting(true);
    setError(null);
    try {
      await api.delete(`/emails/${emailId}`);
      navigate("/emails");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to delete email",
      );
      setShowDeleteConfirm(false);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error && !email)
    return <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>;
  if (!email) return null;

  const parsedResult = email.ai_raw_output as
    | (ParsedEmailResult & Partial<EmissionExtraction>)
    | null;
  const lineItems = parsedResult?.line_items ?? [];
  const emissionExtraction = parsedResult as EmissionExtraction | null;
  const fuelEntries = emissionExtraction?.fuel_entries ?? [];
  const isEmissionEmail =
    (parsedResult &&
      "fuel_entries" in parsedResult &&
      Array.isArray(parsedResult.fuel_entries)) ||
    !!resolvedEmissionReportId;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link
            to="/emails"
            className="mb-2 inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          >
            &larr; Back to Emails
          </Link>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            {email.subject ?? "No Subject"}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={email.processing_status} />
          {(email.processing_status === "pending" ||
            email.processing_status === "failed") && (
            <button
              onClick={handleParse}
              disabled={parsing || polling}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {parsing || polling
                ? "Parsing..."
                : email.processing_status === "failed"
                  ? "Retry parse"
                  : "Parse with AI"}
            </button>
          )}
          {email.processing_status === "failed" && (
            <button
              onClick={handleMarkInvalid}
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              Mark Invalid
            </button>
          )}
          {hasAdminUsers && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-100 dark:border-red-800 dark:bg-red-950/50 dark:text-red-300 dark:hover:bg-red-900/50"
            >
              Delete email
            </button>
          )}
        </div>
      </div>

      {showDeleteConfirm && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          role="dialog"
          aria-modal="true"
          aria-labelledby="delete-email-title"
        >
          <div className="mx-4 max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-slate-900 dark:border dark:border-slate-700">
            <h2
              id="delete-email-title"
              className="text-lg font-semibold text-slate-800 dark:text-slate-100"
            >
              Delete email
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
              Are you sure you want to delete this email? This cannot be undone.
            </p>
            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={deleting}
                className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700 disabled:opacity-50"
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
      )}

      {polling && parseJob && (
        <div className="mb-4 rounded-lg bg-blue-50 p-4 text-blue-700 dark:bg-blue-950/50 dark:text-blue-300">
          <div className="flex items-center gap-2">
            <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
              />
            </svg>
            Parsing in progress... Status: {parseJob.status}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <h2 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
            Email Details
          </h2>
          <dl className="space-y-3">
            <div>
              <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">From</dt>
              <dd className="text-sm text-slate-800 dark:text-slate-200">{email.sender ?? "—"}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">External ID</dt>
              <dd className="truncate text-sm text-slate-800 dark:text-slate-200">
                {email.external_id}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Received</dt>
              <dd className="text-sm text-slate-800 dark:text-slate-200">
                {email.received_at
                  ? new Date(email.received_at).toLocaleString()
                  : "—"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">
                Prompt Version
              </dt>
              <dd className="text-sm text-slate-800 dark:text-slate-200">
                {email.prompt_version ?? "—"}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Retries</dt>
              <dd className="text-sm text-slate-800 dark:text-slate-200">{email.retry_count}</dd>
            </div>
            {email.error_reason && (
              <div>
                <dt className="text-sm font-medium text-red-600">Error</dt>
                <dd className="text-sm text-red-700">{email.error_reason}</dd>
              </div>
            )}
          </dl>
        </div>

        {parsedResult && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
              Parsed Result
            </h2>
            <dl className="space-y-3">
              {parsedResult.summary && (
                <div>
                  <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Summary</dt>
                  <dd className="text-sm text-slate-800 dark:text-slate-200">
                    {parsedResult.summary}
                  </dd>
                </div>
              )}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Vessel</dt>
                  <dd className="text-sm text-slate-800 dark:text-slate-200">
                    {parsedResult.vessel_name ?? "—"}
                    {parsedResult.vessel_imo && (
                      <span className="ml-1 text-slate-500">
                        (IMO: {parsedResult.vessel_imo})
                      </span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">Port</dt>
                  <dd className="text-sm text-slate-800 dark:text-slate-200">
                    {parsedResult.port_name ?? "—"}
                    {parsedResult.port_code && (
                      <span className="ml-1 text-slate-500">
                        ({parsedResult.port_code})
                      </span>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">ETA</dt>
                  <dd className="text-sm text-slate-800 dark:text-slate-200">
                    {parsedResult.eta
                      ? new Date(parsedResult.eta).toLocaleString()
                      : "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">ETD</dt>
                  <dd className="text-sm text-slate-800 dark:text-slate-200">
                    {parsedResult.etd
                      ? new Date(parsedResult.etd).toLocaleString()
                      : "—"}
                  </dd>
                </div>
              </div>
            </dl>

            {isEmissionEmail && (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">
                      Report date
                    </dt>
                    <dd className="text-sm text-slate-800 dark:text-slate-200">
                      {emissionExtraction?.report_date
                        ? new Date(
                            emissionExtraction.report_date,
                          ).toLocaleDateString()
                        : "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">
                      Distance (nm)
                    </dt>
                    <dd className="text-sm text-slate-800 dark:text-slate-200">
                      {emissionExtraction?.distance_nm != null
                        ? emissionExtraction.distance_nm.toLocaleString(
                            undefined,
                            { maximumFractionDigits: 2 },
                          )
                        : "—"}
                    </dd>
                  </div>
                </div>
                <div className="mt-4">
                  <h3 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
                    Fuel entries
                  </h3>
                  <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
                    <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
                      <thead className="bg-slate-50 dark:bg-slate-800/80">
                        <tr>
                          <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">
                            Fuel type
                          </th>
                          <th className="px-4 py-2 text-right font-medium text-slate-600 dark:text-slate-300">
                            Consumption (MT)
                          </th>
                          <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">
                            Status
                          </th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                        {fuelEntries.map((entry, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-2 text-slate-800 dark:text-slate-200">
                              {entry.fuel_type}
                            </td>
                            <td className="px-4 py-2 text-right text-slate-800 dark:text-slate-200">
                              {entry.consumption_mt.toLocaleString(undefined, {
                                maximumFractionDigits: 3,
                              })}
                            </td>
                            <td className="px-4 py-2 text-slate-600 dark:text-slate-300">
                              {entry.operational_status}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
                {emissionReport && (
                  <div className="mb-4 mt-4 flex flex-wrap items-center gap-4">
                    <div>
                      <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                        CO₂:{" "}
                      </span>
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {emissionReport.co2_mt.toLocaleString(undefined, {
                          maximumFractionDigits: 2,
                        })}{" "}
                        MT
                      </span>
                    </div>
                    <div>
                      <span className="text-sm font-medium text-slate-500 dark:text-slate-400">
                        EUA estimate:{" "}
                      </span>
                      <span className="text-sm font-semibold text-slate-800 dark:text-slate-200">
                        {emissionReport.eua_estimate_eur != null
                          ? `€${emissionReport.eua_estimate_eur.toLocaleString(
                              undefined,
                              { maximumFractionDigits: 2 },
                            )}`
                          : "—"}
                      </span>
                    </div>
                    <Badge
                      variant={
                        emissionReport.compliance_status === "green"
                          ? "success"
                          : emissionReport.compliance_status === "yellow"
                            ? "warning"
                            : "destructive"
                      }
                    >
                      {emissionReport.compliance_status}
                    </Badge>
                  </div>
                )}
                {resolvedEmissionReportId && (
                  <div className="mb-4">
                    <Link
                      to={`/emissions/reports/${resolvedEmissionReportId}`}
                      className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
                    >
                      View emission report
                    </Link>
                  </div>
                )}
              </>
            )}
            {lineItems.length > 0 && (
              <div className="mt-4">
                <h3 className="mb-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Line Items
                </h3>
                <div className="overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
                  <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
                    <thead className="bg-slate-50 dark:bg-slate-800/80">
                      <tr>
                        <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">
                          Description
                        </th>
                        <th className="px-4 py-2 text-right font-medium text-slate-600 dark:text-slate-300">
                          Amount
                        </th>
                        <th className="px-4 py-2 text-left font-medium text-slate-600 dark:text-slate-300">
                          Currency
                        </th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                      {lineItems.map((item, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-2 text-slate-800 dark:text-slate-200">
                            {item.description}
                          </td>
                          <td className="px-4 py-2 text-right text-slate-800 dark:text-slate-200">
                            {item.amount.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                            })}
                          </td>
                          <td className="px-4 py-2 text-slate-600 dark:text-slate-300">
                            {item.currency}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                    {(parsedResult?.total_amount ?? null) != null && (
                      <tfoot className="bg-slate-50 dark:bg-slate-800/80">
                        <tr>
                          <td className="px-4 py-2 font-semibold text-slate-800 dark:text-slate-200">
                            Total
                          </td>
                          <td className="px-4 py-2 text-right font-semibold text-slate-800 dark:text-slate-200">
                            {(parsedResult?.total_amount ?? 0).toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                            })}
                          </td>
                          <td className="px-4 py-2 text-slate-600 dark:text-slate-300">
                            {parsedResult?.currency ?? ""}
                          </td>
                        </tr>
                      </tfoot>
                    )}
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {!parsedResult && email.processing_status !== "pending" && (
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <h2 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
              Parsed Result
            </h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              {email.processing_status === "processing"
                ? "Parsing in progress..."
                : "No parsed data available"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
