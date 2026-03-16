import { useState, useEffect, useCallback } from "react";
import { Link, useSearchParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  TariffResponse,
  PortResponse,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { TariffFormModal } from "@/components/TariffFormModal";
import { ArrowLeft, Pencil, Plus } from "lucide-react";

export function TariffConfig() {
  const [searchParams] = useSearchParams();
  const portId = searchParams.get("port_id");

  const [port, setPort] = useState<PortResponse | null>(null);
  const [tariffs, setTariffs] = useState<TariffResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTariff, setEditingTariff] = useState<TariffResponse | null>(null);

  const fetchData = useCallback(async () => {
    if (!portId) return;
    setLoading(true);
    try {
      const [portRes, tariffsRes] = await Promise.all([
        api.get<{ data: PortResponse }>(`/ports/${portId}`),
        api.get<PaginatedResponse<TariffResponse>>("/tariffs", {
          params: { port_id: portId, per_page: 50 },
        }),
      ]);
      setPort(portRes.data.data);
      setTariffs(tariffsRes.data.data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Failed to load tariff configuration",
      );
    } finally {
      setLoading(false);
    }
  }, [portId]);

  useEffect(() => {
    if (!portId) {
      setLoading(false);
      setError("No port selected. Select a port from the Port Directory.");
      return;
    }
    fetchData();
  }, [portId, fetchData]);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" asChild>
            <Link to="/directory/ports" aria-label="Back to Port Directory">
              <ArrowLeft className="size-4" />
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
              Tariff Configuration
            </h1>
            {port && (
              <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                {port.name} ({port.code})
              </p>
            )}
          </div>
        </div>
        {portId && (
          <Button
            onClick={() => {
              setEditingTariff(null);
              setModalOpen(true);
            }}
          >
            <Plus className="size-4" />
            Add Tariff
          </Button>
        )}
      </div>

      {error ? (
        <div className="rounded-lg border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-slate-600 dark:text-slate-300">{error}</p>
          <Link
            to="/directory/ports"
            className="mt-4 inline-flex text-sm font-medium text-mint-600 hover:text-mint-500 dark:text-mint-400"
          >
            ← Back to Port Directory
          </Link>
        </div>
      ) : (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-900">
          {tariffs.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-4 p-8 text-center">
              <p className="text-slate-500 dark:text-slate-400">
                No tariffs configured for this port yet.
              </p>
              <Button
                onClick={() => {
                  setEditingTariff(null);
                  setModalOpen(true);
                }}
              >
                <Plus className="size-4" />
                Add Tariff
              </Button>
            </div>
          ) : (
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Name
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Version
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Valid From
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Valid To
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {tariffs.map((t) => (
                  <tr
                    key={t.id}
                    className="border-b border-slate-100 transition-colors hover:bg-slate-50/50 dark:border-slate-700/50 dark:hover:bg-slate-800/30"
                  >
                    <td className="px-4 py-3 font-medium text-slate-800 dark:text-slate-200">
                      {t.name}
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      v{t.version}
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {new Date(t.valid_from).toLocaleDateString()}
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {t.valid_to
                        ? new Date(t.valid_to).toLocaleDateString()
                        : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-8"
                        onClick={() => {
                          setEditingTariff(t);
                          setModalOpen(true);
                        }}
                        aria-label={`Edit ${t.name}`}
                      >
                        <Pencil className="size-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {portId && (
        <TariffFormModal
          open={modalOpen}
          onOpenChange={setModalOpen}
          portId={portId}
          tariff={editingTariff}
          onSuccess={fetchData}
        />
      )}
    </div>
  );
}
