import { useState, useEffect, useCallback } from "react";
import { Link, useParams } from "react-router";
import { Download, ExternalLink, AlertTriangle } from "lucide-react";
import axios from "axios";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  EmissionReportDetailResponse,
} from "@/api/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Alert, AlertDescription } from "@/components/ui/alert";

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

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function EmissionsReportDetail() {
  const { id } = useParams();
  const [report, setReport] = useState<EmissionReportDetailResponse | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [exportLoading, setExportLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadReport = useCallback(() => {
    if (!id) return;
    api
      .get<SingleResponse<EmissionReportDetailResponse>>(
        `/emissions/reports/${id}`,
      )
      .then((res) => setReport(res.data.data))
      .catch((err) => {
        if (axios.isAxiosError(err) && err.response?.status === 404) {
          setError(
            "Report not found. The emissions API may not be available yet (Tasks 9.1–9.6).",
          );
        } else {
          setError(
            err instanceof ApiError ? err.message : "Failed to load report",
          );
        }
      })
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    loadReport();
  }, [loadReport]);

  async function handleExport(format: "json" | "xml" | "pdf") {
    if (!id) return;
    setExportLoading(format);

    if (format === "json" && report) {
      const blob = new Blob([JSON.stringify(report, null, 2)], {
        type: "application/json",
      });
      downloadBlob(blob, `emission-report-${id.slice(0, 8)}.json`);
      setExportLoading(null);
      return;
    }

    try {
      const res = await api.get(`/emissions/reports/${id}/export`, {
        params: { format },
        responseType: "blob",
      });
      const blob = res.data as Blob;
      const ext = format === "pdf" ? "pdf" : format;
      downloadBlob(blob, `emission-report-${id.slice(0, 8)}.${ext}`);
    } catch (err) {
      if (format === "xml" || format === "pdf") {
        setError(
          err instanceof ApiError
            ? err.message
            : `Export as ${format.toUpperCase()} requires backend support`,
        );
      }
    } finally {
      setExportLoading(null);
    }
  }

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="space-y-4">
        <Link
          to="/emissions"
          className="inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
        >
          &larr; Back to Emissions Dashboard
        </Link>
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  if (!report) return null;

  const complianceVariant =
    COMPLIANCE_VARIANT[report.compliance_status] ?? "outline";
  const verificationVariant =
    VERIFICATION_VARIANT[report.verification_status] ?? "outline";

  return (
    <div className="space-y-6">
      <div>
        <Link
          to="/emissions"
          className="mb-2 inline-block text-sm text-mint-500 hover:text-mint-400"
        >
          &larr; Back to Emissions Dashboard
        </Link>
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              Emission Report
            </h1>
            <p className="mt-1 text-sm text-muted-foreground">
              {report.vessel_name ?? "Vessel"} &middot;{" "}
              {new Date(report.report_date).toLocaleDateString()} &middot;{" "}
              {report.id.slice(0, 8)}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {report.source_email_id && (
              <Button variant="outline" size="sm" asChild>
                <Link
                  to={`/emails/${report.source_email_id}`}
                  className="inline-flex items-center gap-2.5"
                >
                  <ExternalLink className="size-4" />
                  Source email
                </Link>
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("json")}
              disabled={!!exportLoading}
            >
              <Download className="size-4" />
              {exportLoading === "json" ? "Exporting…" : "JSON"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("xml")}
              disabled={!!exportLoading}
            >
              <Download className="size-4" />
              {exportLoading === "xml" ? "Exporting…" : "XML"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("pdf")}
              disabled={!!exportLoading}
            >
              <Download className="size-4" />
              {exportLoading === "pdf" ? "Exporting…" : "PDF"}
            </Button>
          </div>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              CO₂ (MT)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">
              {report.co2_mt.toLocaleString(undefined, {
                minimumFractionDigits: 2,
              })}
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
              {report.eua_estimate_eur != null
                ? report.eua_estimate_eur.toLocaleString(undefined, {
                    minimumFractionDigits: 2,
                  })
                : "—"}
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
            <Badge variant={complianceVariant}>
              {report.compliance_status === "green"
                ? "Within target"
                : report.compliance_status === "yellow"
                  ? "Approaching"
                  : "Over target"}
            </Badge>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Badge variant={verificationVariant}>
              {report.verification_status}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Anomaly flags */}
      {report.anomaly_flags && report.anomaly_flags.length > 0 && (
        <Alert variant="destructive">
          <AlertTriangle className="size-4" />
          <AlertDescription>
            <div className="space-y-1">
              <p className="font-medium">Anomalies detected</p>
              <ul className="list-inside list-disc text-sm">
                {report.anomaly_flags.map((flag, idx) => (
                  <li key={idx}>
                    {flag.code}: {flag.message}
                  </li>
                ))}
              </ul>
            </div>
          </AlertDescription>
        </Alert>
      )}

      {/* Fuel breakdown */}
      <Card>
        <CardHeader>
          <CardTitle>Fuel breakdown</CardTitle>
          <CardDescription>
            Consumption and CO₂ by fuel type
          </CardDescription>
        </CardHeader>
        <CardContent>
          {report.fuel_breakdown && report.fuel_breakdown.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200 dark:border-slate-700">
                    <th className="px-4 py-3 text-left font-medium text-muted-foreground">
                      Fuel type
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                      Consumption (MT)
                    </th>
                    <th className="px-4 py-3 text-right font-medium text-muted-foreground">
                      CO₂ (MT)
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                  {report.fuel_breakdown.map((row, idx) => (
                    <tr key={idx}>
                      <td className="px-4 py-3 font-medium">{row.fuel_type}</td>
                      <td className="px-4 py-3 text-right">
                        {row.consumption_mt.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {row.co2_mt.toLocaleString(undefined, {
                          minimumFractionDigits: 2,
                        })}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No fuel breakdown available
            </p>
          )}
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Report details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm">
          <p>
            <span className="font-medium text-muted-foreground">Vessel:</span>{" "}
            {report.vessel_name ?? "—"} (IMO: {report.vessel_imo ?? "—"})
          </p>
          <p>
            <span className="font-medium text-muted-foreground">Report date:</span>{" "}
            {new Date(report.report_date).toLocaleDateString()}
          </p>
          <p>
            <span className="font-medium text-muted-foreground">Created:</span>{" "}
            {new Date(report.created_at).toLocaleString()}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
