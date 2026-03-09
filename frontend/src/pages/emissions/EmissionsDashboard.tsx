import { useState, useEffect, useCallback, useRef } from "react";
import { Link, useNavigate, useSearchParams, useLocation } from "react-router";
import { Leaf, FileText, ExternalLink } from "lucide-react";
import axios from "axios";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  SingleResponse,
  EmissionReportListResponse,
  EmissionsSummaryResponse,
} from "@/api/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Pagination } from "@/components/Pagination";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { DataTable, type Column } from "@/components/DataTable";
import { EMISSION_REPORT_CREATED } from "@/events/emissions";

const COMPLIANCE_VARIANT: Record<
  "green" | "yellow" | "red",
  "success" | "warning" | "destructive"
> = {
  green: "success",
  yellow: "warning",
  red: "destructive",
};

const VERIFICATION_VARIANT: Record<
  "verified" | "flagged" | "pending",
  "success" | "destructive" | "warning"
> = {
  verified: "success",
  flagged: "destructive",
  pending: "warning",
};

function ComplianceBadge({ status }: { status: "green" | "yellow" | "red" }) {
  const variant = COMPLIANCE_VARIANT[status];
  const label =
    status === "green"
      ? "Within target"
      : status === "yellow"
        ? "Approaching"
        : "Over target";
  return <Badge variant={variant}>{label}</Badge>;
}

function VerificationBadge({
  status,
}: {
  status: "verified" | "flagged" | "pending";
}) {
  const variant = VERIFICATION_VARIANT[status];
  return <Badge variant={variant}>{status}</Badge>;
}

const columns: Column<EmissionReportListResponse>[] = [
  {
    key: "report_date",
    header: "Date",
    render: (value) =>
      value ? new Date(String(value)).toLocaleDateString() : "—",
  },
  {
    key: "vessel_name",
    header: "Vessel",
    render: (value) => String(value ?? "—"),
  },
  {
    key: "co2_mt",
    header: "CO₂ (MT)",
    render: (value) =>
      typeof value === "number"
        ? value.toLocaleString(undefined, { minimumFractionDigits: 2 })
        : "—",
  },
  {
    key: "eua_estimate_eur",
    header: "EUA Est. (€)",
    render: (value) =>
      value != null
        ? Number(value).toLocaleString(undefined, {
            minimumFractionDigits: 2,
          })
        : "—",
  },
  {
    key: "compliance_status",
    header: "Compliance",
    render: (value) => (
      <ComplianceBadge status={value as "green" | "yellow" | "red"} />
    ),
  },
  {
    key: "verification_status",
    header: "Status",
    render: (value) => (
      <VerificationBadge
        status={value as "verified" | "flagged" | "pending"}
      />
    ),
  },
  {
    key: "source_email_id",
    header: "Source",
    render: (value, item) =>
      value ? (
        <Link
          to={`/emails/${value}`}
          className="inline-flex items-center gap-2.5 text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          onClick={(e) => e.stopPropagation()}
        >
          Email
          <ExternalLink className="size-4" />
        </Link>
      ) : (
        "—"
      ),
  },
];

export function EmissionsDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [summary, setSummary] = useState<EmissionsSummaryResponse | null>(null);
  const [reports, setReports] = useState<EmissionReportListResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [apiUnavailable, setApiUnavailable] = useState(false);
  const mountedRef = useRef(true);

  const page = Number(searchParams.get("page") ?? "1");
  const vesselFilter = searchParams.get("vessel") ?? "";
  const statusFilter = searchParams.get("status") ?? "";
  const dateFrom = searchParams.get("date_from") ?? "";
  const dateTo = searchParams.get("date_to") ?? "";

  const fetchData = useCallback(() => {
    if (!mountedRef.current) return;
    setLoading(true);
    const params: Record<string, string | number> = {
      page,
      per_page: 20,
    };
    if (vesselFilter) params.vessel_id = vesselFilter;
    if (statusFilter) params.verification_status = statusFilter;
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;

    const summaryParams: Record<string, string> = {};
    if (vesselFilter) summaryParams.vessel_id = vesselFilter;
    if (dateFrom) summaryParams.date_from = dateFrom;
    if (dateTo) summaryParams.date_to = dateTo;

    setApiUnavailable(false);
    Promise.all([
      api
        .get<SingleResponse<EmissionsSummaryResponse>>("/emissions/summary", {
          params: summaryParams,
        })
        .then((res) => {
          if (mountedRef.current) {
            setSummary(res.data.data);
            setApiUnavailable(false);
          }
        })
        .catch((err) => {
          if (mountedRef.current) {
            setSummary(null);
            if (axios.isAxiosError(err) && err.response?.status === 404) {
              setApiUnavailable(true);
            }
          }
        }),
      api
        .get<PaginatedResponse<EmissionReportListResponse>>(
          "/emissions/reports",
          { params },
        )
        .then((res) => {
          if (mountedRef.current) {
            setReports(res.data.data);
            setTotal(res.data.meta.total);
          }
        })
        .catch((err) => {
          if (mountedRef.current) {
            if (axios.isAxiosError(err) && err.response?.status === 404) {
              setReports([]);
              setTotal(0);
              setError(null);
              setApiUnavailable(true);
            } else {
              setError(
                err instanceof ApiError ? err.message : "Failed to load reports",
              );
            }
          }
        }),
    ]).finally(() => {
      if (mountedRef.current) setLoading(false);
    });
  }, [page, vesselFilter, statusFilter, dateFrom, dateTo]);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData, location.key]);

  useEffect(() => {
    const handleEmissionReportCreated = () => {
      fetchData();
    };
    window.addEventListener(EMISSION_REPORT_CREATED, handleEmissionReportCreated);
    return () =>
      window.removeEventListener(
        EMISSION_REPORT_CREATED,
        handleEmissionReportCreated,
      );
  }, [fetchData]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") {
        fetchData();
      }
    };
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () =>
      document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [fetchData]);

  function updateFilter(key: string, value: string) {
    const params = new URLSearchParams(searchParams);
    if (value) params.set(key, value);
    else params.delete(key);
    params.set("page", "1");
    setSearchParams(params);
  }

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );

  return (
    <div className="space-y-6">
      <header>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-emerald-100 p-2 dark:bg-emerald-900/50">
            <Leaf className="size-6 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Emissions Dashboard
            </h1>
            <p className="text-sm text-muted-foreground">
              Carbon debt, compliance status, and emission reports
            </p>
          </div>
        </div>
      </header>

      {apiUnavailable && (
        <Alert>
          <AlertDescription>
            Emissions API is not available yet. The dashboard will show data once
            the backend (Tasks 9.1–9.6) is deployed.
          </AlertDescription>
        </Alert>
      )}

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Total CO₂ (MT)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {summary?.total_co2_mt?.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              }) ?? "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              EUA Est. (€)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {summary?.total_eua_estimate_eur != null
                ? summary.total_eua_estimate_eur.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                  })
                : "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Voyages
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {summary?.voyage_count ?? "—"}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-4">
              {summary?.compliance ? (
                <>
                  <span className="inline-flex items-center gap-2.5 text-sm">
                    <span className="size-2.5 rounded-full bg-green-500" />
                    {summary.compliance.green}
                  </span>
                  <span className="inline-flex items-center gap-2.5 text-sm">
                    <span className="size-2.5 rounded-full bg-amber-500" />
                    {summary.compliance.yellow}
                  </span>
                  <span className="inline-flex items-center gap-2.5 text-sm">
                    <span className="size-2.5 rounded-full bg-red-500" />
                    {summary.compliance.red}
                  </span>
                </>
              ) : (
                "—"
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity logs */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Activity Logs</CardTitle>
          <CardAction>
            <div className="flex flex-wrap items-center gap-3">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => updateFilter("date_from", e.target.value)}
                className="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm dark:bg-slate-800 dark:text-slate-100"
              />
              <span className="text-muted-foreground">to</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => updateFilter("date_to", e.target.value)}
                className="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm dark:bg-slate-800 dark:text-slate-100"
              />
              <select
                value={statusFilter}
                onChange={(e) => updateFilter("status", e.target.value)}
                className="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm dark:bg-slate-800 dark:text-slate-100"
              >
                <option value="">All statuses</option>
                <option value="verified">Verified</option>
                <option value="flagged">Flagged</option>
                <option value="pending">Pending</option>
              </select>
            </div>
          </CardAction>
        </CardHeader>
        <CardContent>
          {reports.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="size-12 text-muted-foreground" />
              <p className="mt-4 text-sm font-medium text-muted-foreground">
                No emission reports yet
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                Reports are generated from noon bunker reports and arrival emails
              </p>
            </div>
          ) : (
            <>
              <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
                <DataTable
                  data={reports}
                  columns={columns}
                  keyExtractor={(r) => r.id}
                  onRowClick={(r) => navigate(`/emissions/reports/${r.id}`)}
                />
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
        </CardContent>
      </Card>
    </div>
  );
}
