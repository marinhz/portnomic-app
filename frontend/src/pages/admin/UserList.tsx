import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";
import api, { ApiError } from "@/api/client";
import type { PaginatedResponse, UserResponse } from "@/api/types";
import { DataTable, type Column } from "@/components/DataTable";
import { Pagination } from "@/components/Pagination";
import { LoadingSpinner } from "@/components/LoadingSpinner";

const columns: Column<UserResponse>[] = [
  { key: "email", header: "Email" },
  {
    key: "is_active",
    header: "Active",
    render: (value) => (
      <span
        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
          value ? "bg-green-50 text-green-700 dark:bg-green-900/50 dark:text-green-300" : "bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300"
        }`}
      >
        {value ? "Yes" : "No"}
      </span>
    ),
  },
  {
    key: "mfa_enabled",
    header: "MFA",
    render: (value) => (
      <span
        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
          value ? "bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300" : "bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400"
        }`}
      >
        {value ? "Enabled" : "Disabled"}
      </span>
    ),
  },
  {
    key: "created_at",
    header: "Created",
    render: (value) => new Date(String(value)).toLocaleDateString(),
  },
];

export function UserList() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api
      .get<PaginatedResponse<UserResponse>>("/admin/users", {
        params: { page, per_page: 20 },
      })
      .then((res) => {
        setUsers(res.data.data);
        setTotalPages(Math.ceil(res.data.meta.total / res.data.meta.per_page));
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load users",
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
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Users</h1>
        <Link
          to="/admin/users/new"
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          New User
        </Link>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <DataTable
          data={users}
          columns={columns}
          keyExtractor={(u) => u.id}
          onRowClick={(u) => navigate(`/admin/users/${u.id}/edit`)}
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
