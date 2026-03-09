import { useState, useEffect } from "react";
import { Link, useNavigate, useSearchParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  PortCallResponse,
  VesselResponse,
} from "@/api/types";
import { DataTable, type Column } from "@/components/DataTable";
import { Pagination } from "@/components/Pagination";
import { LoadingSpinner } from "@/components/LoadingSpinner";

const PORT_CALL_STATUSES = [
  "Planned",
  "Arrived",
  "Berthed",
  "Departed",
  "Cancelled",
];

export function PortCallList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const statusFromUrl = searchParams.get("status") ?? "";
  const [portCalls, setPortCalls] = useState<PortCallResponse[]>([]);
  const [vessels, setVessels] = useState<VesselResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [filterVesselId, setFilterVesselId] = useState("");
  const [filterStatus, setFilterStatus] = useState(statusFromUrl);

  useEffect(() => {
    setFilterStatus(statusFromUrl);
  }, [statusFromUrl]);

  useEffect(() => {
    api
      .get<PaginatedResponse<VesselResponse>>("/vessels", {
        params: { per_page: 200 },
      })
      .then((res) => setVessels(res.data.data))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setLoading(true);
    const params: Record<string, string | number> = {
      page,
      per_page: 20,
    };
    if (filterVesselId) params.vessel_id = filterVesselId;
    if (filterStatus) params.status = filterStatus;

    api
      .get<PaginatedResponse<PortCallResponse>>("/port-calls", { params })
      .then((res) => {
        setPortCalls(res.data.data);
        setTotalPages(Math.ceil(res.data.meta.total / res.data.meta.per_page));
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load port calls",
        );
      })
      .finally(() => setLoading(false));
  }, [page, filterVesselId, filterStatus]);

  const columns: Column<PortCallResponse>[] = [
    {
      key: "vessel_id",
      header: "Vessel",
      render: (value) => {
        const v = vessels.find((vsl) => vsl.id === String(value));
        return v ? v.name : String(value).slice(0, 8) + "...";
      },
    },
    {
      key: "eta",
      header: "ETA",
      render: (value) => (value ? new Date(String(value)).toLocaleDateString() : "—"),
    },
    {
      key: "etd",
      header: "ETD",
      render: (value) => (value ? new Date(String(value)).toLocaleDateString() : "—"),
    },
    {
      key: "status",
      header: "Status",
      render: (value) => <StatusBadge status={String(value)} />,
    },
    {
      key: "created_at",
      header: "Created",
      render: (value) => new Date(String(value)).toLocaleDateString(),
    },
  ];

  const selectClass =
    "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100";

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Port Calls</h1>
        <Link
          to="/port-calls/new"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          New Port Call
        </Link>
      </div>

      <div className="mb-4 flex flex-wrap gap-3">
        <select
          value={filterVesselId}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
            setFilterVesselId(e.target.value);
            setPage(1);
          }}
          className={selectClass}
        >
          <option value="">All Vessels</option>
          {vessels.map((v) => (
            <option key={v.id} value={v.id}>
              {v.name}
            </option>
          ))}
        </select>

        <select
          value={filterStatus}
          onChange={(e: React.ChangeEvent<HTMLSelectElement>) => {
            setFilterStatus(e.target.value);
            setPage(1);
          }}
          className={selectClass}
        >
          <option value="">All Statuses</option>
          {PORT_CALL_STATUSES.map((s) => (
            <option key={s} value={s.toLowerCase()}>
              {s}
            </option>
          ))}
        </select>
      </div>

      {error ? (
        <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
      ) : loading ? (
        <LoadingSpinner />
      ) : (
        <>
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
            <DataTable
              data={portCalls}
              columns={columns}
              keyExtractor={(pc) => pc.id}
              onRowClick={(pc) => navigate(`/port-calls/${pc.id}`)}
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
        </>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    planned: "bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300",
    arrived: "bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300",
    berthed: "bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-300",
    departed: "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
    cancelled: "bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300",
  };
  const colors =
    colorMap[status.toLowerCase()] ?? "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
  return (
    <span
      className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${colors}`}
    >
      {status}
    </span>
  );
}
