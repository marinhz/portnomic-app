import { useState, useEffect } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  SingleResponse,
  VesselResponse,
  PortCallResponse,
  PortResponse,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";

const PORT_CALL_STATUSES = [
  "scheduled",
  "arrived",
  "berthed",
  "departed",
  "cancelled",
];

export function PortCallForm() {
  const { portCallId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const isEdit = !!portCallId;

  const [vesselId, setVesselId] = useState(
    searchParams.get("vessel_id") ?? "",
  );
  const [portId, setPortId] = useState("");
  const [eta, setEta] = useState("");
  const [etd, setEtd] = useState("");
  const [status, setStatus] = useState("scheduled");

  const [vessels, setVessels] = useState<VesselResponse[]>([]);
  const [ports, setPorts] = useState<PortResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [vesselsRes, portsRes] = await Promise.all([
          api.get<PaginatedResponse<VesselResponse>>("/vessels", {
            params: { per_page: 200 },
          }),
          api.get<PaginatedResponse<PortResponse>>("/ports", {
            params: { per_page: 200 },
          }),
        ]);
        setVessels(vesselsRes.data.data);
        setPorts(portsRes.data.data);

        if (portCallId) {
          const pcRes = await api.get<SingleResponse<PortCallResponse>>(
            `/port-calls/${portCallId}`,
          );
          const pc = pcRes.data.data;
          setVesselId(pc.vessel_id);
          setPortId(pc.port_id);
          setEta(pc.eta ? pc.eta.split("T")[0] : "");
          setEtd(pc.etd ? pc.etd.split("T")[0] : "");
          setStatus(pc.status);
        }
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load data",
        );
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [portCallId]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const payload = {
      vessel_id: vesselId,
      port_id: portId,
      eta: eta || undefined,
      etd: etd || undefined,
      status,
    };

    try {
      if (isEdit) {
        await api.put(`/port-calls/${portCallId}`, payload);
      } else {
        await api.post("/port-calls", payload);
      }
      navigate("/port-calls");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to save port call",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  const inputClass =
    "w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-2.5 text-sm text-slate-900 dark:text-slate-100 placeholder:text-slate-500 dark:placeholder:text-slate-400 transition-colors focus:border-mint-500 focus:outline-none focus:ring-2 focus:ring-mint-500/20";

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-800 dark:text-slate-100">
        {isEdit ? "Edit Port Call" : "New Port Call"}
      </h1>

      <div className="mx-auto max-w-2xl rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        {error && (
          <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/30 p-3 text-sm text-red-700 dark:text-red-200">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="vessel"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Vessel
            </label>
            <select
              id="vessel"
              value={vesselId}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setVesselId(e.target.value)
              }
              required
              className={inputClass}
            >
              <option value="">Select vessel...</option>
              {vessels.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name} {v.imo ? `(IMO: ${v.imo})` : ""}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label
              htmlFor="port"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Port
            </label>
            <select
              id="port"
              value={portId}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setPortId(e.target.value)
              }
              required
              className={inputClass}
            >
              <option value="">Select port...</option>
              {ports.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.code})
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="eta"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                ETA
              </label>
              <input
                id="eta"
                type="date"
                value={eta}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setEta(e.target.value)
                }
                required
                className={inputClass}
              />
            </div>

            <div>
              <label
                htmlFor="etd"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                ETD
              </label>
              <input
                id="etd"
                type="date"
                value={etd}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setEtd(e.target.value)
                }
                required
                className={inputClass}
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="status"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Status
            </label>
            <select
              id="status"
              value={status}
              onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                setStatus(e.target.value)
              }
              required
              className={inputClass}
            >
              {PORT_CALL_STATUSES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting
                ? "Saving..."
                : isEdit
                  ? "Update Port Call"
                  : "Create Port Call"}
            </button>
            <button
              type="button"
              onClick={() => navigate("/port-calls")}
              className="rounded-lg border border-slate-300 dark:border-slate-600 px-6 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-300 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
