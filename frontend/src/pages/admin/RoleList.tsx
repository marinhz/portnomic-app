import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { Plus } from "lucide-react";
import api, { ApiError } from "@/api/client";
import type { RoleResponse } from "@/api/types";
import { DataTable, type Column } from "@/components/DataTable";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

const columns: Column<RoleResponse>[] = [
  { key: "name", header: "Name" },
  {
    key: "permissions",
    header: "Permissions",
    render: (value) => {
      const perms = value as unknown as string[];
      return (
        <div className="flex flex-wrap gap-2.5">
          {perms.map((p) => (
            <span
              key={p}
              className="rounded bg-mint-100 px-2.5 py-0.5 text-xs font-medium text-navy-800 dark:bg-navy-800 dark:text-mint-200"
            >
              {p}
            </span>
          ))}
        </div>
      );
    },
  },
  {
    key: "created_at",
    header: "Created",
    render: (value) => new Date(String(value)).toLocaleDateString(),
  },
];

export function RoleList() {
  const navigate = useNavigate();
  const [roles, setRoles] = useState<RoleResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<{ data: RoleResponse[] }>("/admin/roles")
      .then((res) => setRoles(res.data.data))
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load roles",
        );
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Roles</h1>
        <Button onClick={() => navigate("/admin/roles/new")}>
          <Plus className="size-4" />
          New Role
        </Button>
      </div>

      <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
        <DataTable
          data={roles}
          columns={columns}
          keyExtractor={(r) => r.id}
          onRowClick={(r) => navigate(`/admin/roles/${r.id}/edit`)}
        />
      </div>
    </div>
  );
}
