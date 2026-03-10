import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type { VesselResponse, SingleResponse } from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";

const VESSEL_TYPES = [
  "Bulk Carrier",
  "Container Ship",
  "Tanker",
  "General Cargo",
  "Ro-Ro",
  "LNG Carrier",
  "Passenger",
  "Tug",
  "Other",
];

export function VesselForm() {
  const { vesselId } = useParams();
  const navigate = useNavigate();
  const isEdit = !!vesselId;

  const [name, setName] = useState("");
  const [imoNumber, setImoNumber] = useState("");
  const [mmsi, setMmsi] = useState("");
  const [vesselType, setVesselType] = useState("");
  const [flag, setFlag] = useState("");

  const [loading, setLoading] = useState(isEdit);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!vesselId) return;
    api
      .get<SingleResponse<VesselResponse>>(`/vessels/${vesselId}`)
      .then((res) => {
        const v = res.data.data;
        setName(v.name);
        setImoNumber(v.imo ?? "");
        setMmsi(v.mmsi ?? "");
        setVesselType(v.vessel_type ?? "");
        setFlag(v.flag ?? "");
      })
      .catch((err) => {
        setError(
          err instanceof ApiError ? err.message : "Failed to load vessel",
        );
      })
      .finally(() => setLoading(false));
  }, [vesselId]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const payload = {
      name,
      imo: imoNumber || undefined,
      mmsi: mmsi || undefined,
      vessel_type: vesselType || undefined,
      flag: flag || undefined,
    };

    try {
      if (isEdit) {
        await api.put(`/vessels/${vesselId}`, payload);
      } else {
        await api.post("/vessels", payload);
      }
      navigate("/vessels");
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to save vessel",
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
        {isEdit ? "Edit Vessel" : "New Vessel"}
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
              htmlFor="name"
              className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
            >
              Vessel Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setName(e.target.value)
              }
              required
              className={inputClass}
              placeholder="MV Ocean Star"
            />
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="imo"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                IMO Number
              </label>
              <input
                id="imo"
                type="text"
                value={imoNumber}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setImoNumber(e.target.value)
                }
                required
                pattern="[0-9]{7}"
                className={inputClass}
                placeholder="1234567"
              />
            </div>

            <div>
              <label
                htmlFor="mmsi"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                MMSI
              </label>
              <input
                id="mmsi"
                type="text"
                value={mmsi}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setMmsi(e.target.value)
                }
                required
                pattern="[0-9]{9}"
                className={inputClass}
                placeholder="123456789"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="type"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Vessel Type
              </label>
              <select
                id="type"
                value={vesselType}
                onChange={(e: React.ChangeEvent<HTMLSelectElement>) =>
                  setVesselType(e.target.value)
                }
                required
                className={inputClass}
              >
                <option value="">Select type...</option>
                {VESSEL_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label
                htmlFor="flag"
                className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300"
              >
                Flag
              </label>
              <input
                id="flag"
                type="text"
                value={flag}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  setFlag(e.target.value)
                }
                required
                className={inputClass}
                placeholder="Panama"
              />
            </div>
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
                  ? "Update Vessel"
                  : "Create Vessel"}
            </button>
            <button
              type="button"
              onClick={() => navigate("/vessels")}
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
