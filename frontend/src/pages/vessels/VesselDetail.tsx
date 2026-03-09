import { useState, useEffect } from "react";
import { Link, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  PaginatedResponse,
  VesselResponse,
  PortCallResponse,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export function VesselDetail() {
  const { vesselId } = useParams();
  const [vessel, setVessel] = useState<VesselResponse | null>(null);
  const [portCalls, setPortCalls] = useState<PortCallResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!vesselId) return;
    async function load() {
      try {
        const [vesselRes, portCallsRes] = await Promise.all([
          api.get<SingleResponse<VesselResponse>>(`/vessels/${vesselId}`),
          api.get<PaginatedResponse<PortCallResponse>>("/port-calls", {
            params: { vessel_id: vesselId, per_page: 50 },
          }),
        ]);
        setVessel(vesselRes.data.data);
        setPortCalls(portCallsRes.data.data);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load vessel",
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [vesselId]);

  if (loading) return <LoadingSpinner />;
  if (error)
    return (
      <div className="rounded-lg bg-red-50 p-4 text-red-700 dark:bg-red-950/50 dark:text-red-300">{error}</div>
    );
  if (!vessel) return null;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <Link
            to="/vessels"
            className="mb-2 inline-block text-sm text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          >
            &larr; Back to Vessels
          </Link>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">{vessel.name}</h1>
        </div>
        <Link
          to={`/vessels/${vesselId}/edit`}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
        >
          Edit Vessel
        </Link>
      </div>

      <div className="mb-6 rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <h2 className="mb-4 text-lg font-semibold text-slate-800 dark:text-slate-100">
          Vessel Details
        </h2>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <DetailField label="IMO Number" value={vessel.imo ?? "N/A"} />
          <DetailField label="MMSI" value={vessel.mmsi ?? "N/A"} />
          <DetailField label="Vessel Type" value={vessel.vessel_type ?? "N/A"} />
          <DetailField label="Flag" value={vessel.flag ?? "N/A"} />
          <DetailField
            label="Created"
            value={new Date(vessel.created_at).toLocaleDateString()}
          />
          <DetailField
            label="Last Updated"
            value={vessel.updated_at ? new Date(vessel.updated_at).toLocaleDateString() : "Never"}
          />
        </dl>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-900">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100">Port Calls</h2>
          <Link
            to={`/port-calls/new?vessel_id=${vesselId}`}
            className="text-sm font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
          >
            New Port Call
          </Link>
        </div>
        {portCalls.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400">
            No port calls for this vessel
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/80">
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Port
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    ETA
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    ETD
                  </th>
                  <th className="px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody>
                {portCalls.map((pc) => (
                  <tr
                    key={pc.id}
                    className="border-b border-slate-100 even:bg-slate-50/50 dark:border-slate-700/50 dark:even:bg-slate-800/30"
                  >
                    <td className="px-4 py-3">
                      <Link
                        to={`/port-calls/${pc.id}`}
                        className="font-medium text-mint-500 hover:text-mint-400 dark:text-mint-400 dark:hover:text-mint-300"
                      >
                        Port Call
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {pc.eta ? new Date(pc.eta).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-4 py-3 text-slate-600 dark:text-slate-300">
                      {pc.etd ? new Date(pc.etd).toLocaleDateString() : "—"}
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={pc.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function DetailField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-sm font-medium text-slate-500 dark:text-slate-400">{label}</dt>
      <dd className="mt-1 text-sm text-slate-800 dark:text-slate-200">{value}</dd>
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
