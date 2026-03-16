import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  PortResponse,
  PortCreate,
} from "@/api/types";
import { DataTable, type Column } from "@/components/DataTable";
import { Pagination } from "@/components/Pagination";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Plus, Settings } from "lucide-react";

const columns: Column<PortResponse>[] = [
  { key: "name", header: "Name" },
  { key: "country", header: "Country" },
  { key: "code", header: "UN/LOCODE" },
  { key: "timezone", header: "Timezone" },
  {
    key: "id",
    header: "Actions",
    render: (_, item) => (
      <Link
        to={`/directory/tariffs?port_id=${item.id}`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-mint-600 hover:text-mint-500 dark:text-mint-400 dark:hover:text-mint-300"
      >
        <Settings className="size-4" />
        Tariff Configuration
      </Link>
    ),
  },
];

export function PortDirectory() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [ports, setPorts] = useState<PortResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  const page = Number(searchParams.get("page") ?? "1");
  const search = searchParams.get("search") ?? "";

  const fetchPorts = useCallback(async () => {
    setLoading(true);
    const params: Record<string, string | number> = {
      page,
      per_page: 20,
    };
    if (search) params.search = search;

    api
      .get<PaginatedResponse<PortResponse>>("/ports", { params })
      .then((res) => {
        setPorts(res.data.data);
        setTotal(res.data.meta.total);
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load ports",
        );
      })
      .finally(() => setLoading(false));
  }, [page, search]);

  useEffect(() => {
    fetchPorts();
  }, [fetchPorts]);

  const handleSearchChange = (value: string) => {
    const params = new URLSearchParams(searchParams);
    if (value) {
      params.set("search", value);
    } else {
      params.delete("search");
    }
    params.set("page", "1");
    setSearchParams(params);
  };

  const handleCreatePort = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setCreateError(null);
    setSubmitting(true);

    const form = e.currentTarget;
    const formData = new FormData(form);
    const name = formData.get("name") as string;
    const code = (formData.get("code") as string).toUpperCase().trim();
    const country = (formData.get("country") as string) || null;
    const timezone = (formData.get("timezone") as string) || null;
    const latStr = (formData.get("latitude") as string) || null;
    const lonStr = (formData.get("longitude") as string) || null;

    const payload: PortCreate = {
      name,
      code,
      country: country || undefined,
      timezone: timezone || undefined,
      latitude: latStr ? parseFloat(latStr) : undefined,
      longitude: lonStr ? parseFloat(lonStr) : undefined,
    };

    try {
      await api.post("/ports", payload);
      setAddModalOpen(false);
      form.reset();
      fetchPorts();
    } catch (err) {
      setCreateError(
        err instanceof ApiError ? err.message : "Failed to create port",
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">
        {error}
      </div>
    );

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
          Port Directory
        </h1>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative">
            <Input
              type="search"
              placeholder="Search by name, code, or country..."
              value={search}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                handleSearchChange(e.target.value)
              }
              className="w-full sm:w-64"
              aria-label="Search ports"
            />
          </div>
          <Button onClick={() => setAddModalOpen(true)}>
            <Plus className="size-4" />
            Add Port
          </Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <DataTable
          data={ports}
          columns={columns}
          keyExtractor={(p) => p.id}
        />
      </div>

      {Math.ceil(total / 20) > 1 && (
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
      )}

      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Port</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreatePort} className="space-y-4">
            {createError && (
              <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 dark:bg-red-900/30 dark:text-red-200">
                {createError}
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="port-name">Name</Label>
              <Input
                id="port-name"
                name="name"
                required
                placeholder="e.g. Rotterdam"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port-country">Country</Label>
              <Input
                id="port-country"
                name="country"
                placeholder="e.g. Netherlands"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="port-code">UN/LOCODE</Label>
              <Input
                id="port-code"
                name="code"
                required
                placeholder="e.g. NLRTM"
                className="uppercase"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="port-lat">Latitude</Label>
                <Input
                  id="port-lat"
                  name="latitude"
                  type="number"
                  step="any"
                  placeholder="51.9225"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="port-lon">Longitude</Label>
                <Input
                  id="port-lon"
                  name="longitude"
                  type="number"
                  step="any"
                  placeholder="4.4792"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="port-timezone">Timezone</Label>
              <Input
                id="port-timezone"
                name="timezone"
                placeholder="e.g. Europe/Amsterdam"
              />
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setAddModalOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {submitting ? "Creating..." : "Create Port"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
