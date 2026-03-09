import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";
import api, { ApiError } from "@/api/client";
import type { PaginatedResponse, VesselResponse } from "@/api/types";
import { DataTable, type Column } from "@/components/DataTable";
import { Pagination } from "@/components/Pagination";
import { LoadingSpinner } from "@/components/LoadingSpinner";

const columns: Column<VesselResponse>[] = [
  { key: "name", header: "Name" },
  { key: "imo", header: "IMO" },
  { key: "mmsi", header: "MMSI" },
  { key: "vessel_type", header: "Type" },
  { key: "flag", header: "Flag" },
  {
    key: "created_at",
    header: "Created",
    render: (value) => new Date(String(value)).toLocaleDateString(),
  },
];

export function VesselList() {
  const navigate = useNavigate();
  const [vessels, setVessels] = useState<VesselResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<PaginatedResponse<VesselResponse>>("/vessels", {
        params: { page, per_page: 20 },
      })
      .then((res) => {
        setVessels(res.data.data);
        setTotalPages(Math.ceil(res.data.meta.total / res.data.meta.per_page));
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load vessels",
        );
      })
      .finally(() => setLoading(false));
  }, [page]);

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
    );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Vessels</h1>
        <Link
          to="/vessels/new"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          New Vessel
        </Link>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <DataTable
          data={vessels}
          columns={columns}
          keyExtractor={(v) => v.id}
          onRowClick={(v) => navigate(`/vessels/${v.id}`)}
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
