import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import {
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  MinusCircle,
} from "lucide-react";
import { toast } from "sonner";
import api, { ApiError } from "@/api/client";
import type { PaginatedResponse, EmailListResponse } from "@/api/types";
import { DataTable, type Column } from "@/components/DataTable";
import { Pagination } from "@/components/Pagination";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";

function StatusBadge({ status }: { status: string }) {
  const { variant, Icon } =
    status === "completed"
      ? { variant: "success" as const, Icon: CheckCircle }
      : status === "failed" || status === "invalid"
        ? { variant: "destructive" as const, Icon: XCircle }
        : status === "processing"
          ? { variant: "info" as const, Icon: AlertCircle }
          : status === "pending"
            ? { variant: "warning" as const, Icon: AlertCircle }
            : { variant: "outline" as const, Icon: MinusCircle };
  return (
    <Badge variant={variant}>
      <Icon className="size-4 shrink-0" />
      {status}
    </Badge>
  );
}

const columns: Column<EmailListResponse>[] = [
  {
    key: "subject",
    header: "Subject",
    render: (value) => (
      <span className="max-w-xs truncate block">{String(value ?? "—")}</span>
    ),
  },
  { key: "sender", header: "From" },
  {
    key: "processing_status",
    header: "Status",
    render: (value) => <StatusBadge status={String(value)} />,
  },
  {
    key: "retry_count",
    header: "Retries",
  },
  {
    key: "received_at",
    header: "Received",
    render: (value) =>
      value ? new Date(String(value)).toLocaleString() : "—",
  },
  {
    key: "created_at",
    header: "Ingested",
    render: (value) => new Date(String(value)).toLocaleString(),
  },
];

export function EmailList() {
  const navigate = useNavigate();
  const [emails, setEmails] = useState<EmailListResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [syncing, setSyncing] = useState(false);

  const fetchEmails = () => {
    setLoading(true);
    const params: Record<string, unknown> = { page, per_page: 20 };
    if (statusFilter) params.status = statusFilter;

    api
      .get<PaginatedResponse<EmailListResponse>>("/emails", { params })
      .then((res) => {
        setEmails(res.data.data);
        setTotalPages(Math.ceil(res.data.meta.total / res.data.meta.per_page));
      })
      .catch((err) => {
        setError(err instanceof ApiError ? err.message : "Failed to load emails");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchEmails();
  }, [page, statusFilter]);

  async function handleCheckNewMail() {
    setSyncing(true);
    try {
      const res = await api.post<{ ingested: number }>(
        "/integrations/email/sync",
      );
      fetchEmails();
      if (res.data.ingested > 0) {
        toast.success(`Found ${res.data.ingested} new email(s).`);
      } else {
        toast.info("No new emails.");
      }
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Failed to check for new mail",
      );
    } finally {
      setSyncing(false);
    }
  }

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Emails</h1>
        <div className="flex items-center gap-4">
          <Button
            variant="outline"
            onClick={handleCheckNewMail}
            disabled={syncing}
          >
            <RefreshCw
              className={`size-4 ${syncing ? "animate-spin" : ""}`}
            />
            {syncing ? "Checking…" : "Check for new mail"}
          </Button>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm dark:bg-slate-800 dark:text-slate-100"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
        <DataTable
          data={emails}
          columns={columns}
          keyExtractor={(e) => e.id}
          onRowClick={(e) => navigate(`/emails/${e.id}`)}
        />
      </div>

      {totalPages > 1 && (
        <div className="mt-4">
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </div>
      )}
    </div>
  );
}
