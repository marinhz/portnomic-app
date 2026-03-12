import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { Plus } from "lucide-react";
import api, { ApiError } from "@/api/client";
import type { RoleResponse } from "@/api/types";
import { getModuleSummary } from "@/lib/permissions";
import { DataTable, type Column } from "@/components/DataTable";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const columns: Column<RoleResponse>[] = [
  { key: "name", header: "Name" },
  {
    key: "permissions",
    header: "Permissions",
    render: (value) => {
      const perms = value as unknown as string[];
      const summary = getModuleSummary(perms);
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            <div className="flex cursor-help flex-wrap gap-x-3 gap-y-1 text-sm">
              {summary.map(({ label, hasAccess }) => (
                <span
                  key={label}
                  className={
                    hasAccess
                      ? "text-slate-700 dark:text-slate-200"
                      : "text-slate-400 dark:text-slate-500"
                  }
                >
                  {label} {hasAccess ? "✓" : "✗"}
                </span>
              ))}
            </div>
          </TooltipTrigger>
          <TooltipContent side="top" className="max-w-xs">
            <div className="space-y-1">
              <p className="font-medium">Full permissions</p>
              <ul className="list-inside list-disc text-xs">
                {perms.length > 0 ? (
                  perms.map((p) => <li key={p}>{p}</li>)
                ) : (
                  <li className="text-slate-400">None</li>
                )}
              </ul>
            </div>
          </TooltipContent>
        </Tooltip>
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
