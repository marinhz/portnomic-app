import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type { SingleResponse, DAResponse } from "@/api/types";

export function DAGenerate() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const portCallId = searchParams.get("port_call_id") ?? "";

  const [daType, setDaType] = useState<"proforma" | "final">("proforma");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!portCallId) {
      setError("Port call ID is required");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await api.post<SingleResponse<DAResponse>>("/da/generate", {
        port_call_id: portCallId,
        type: daType,
      });
      navigate(`/da/${res.data.data.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to generate DA",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-lg">
      <h1 className="mb-6 text-2xl font-bold text-slate-800 dark:text-slate-100">
        Generate Disbursement Account
      </h1>

      <form onSubmit={handleGenerate}>
        <div className="rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
          {error && (
            <div className="mb-4 rounded-lg bg-red-50 dark:bg-red-900/30 p-3 text-sm text-red-700 dark:text-red-200">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Port Call ID
            </label>
            <input
              type="text"
              value={portCallId}
              readOnly
              className="w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 px-3 py-2 text-sm text-slate-500 dark:text-slate-400"
            />
          </div>

          <div className="mb-6">
            <label className="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
              DA Type
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="daType"
                  value="proforma"
                  checked={daType === "proforma"}
                  onChange={() => setDaType("proforma")}
                  className="text-mint-500"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">Proforma</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="radio"
                  name="daType"
                  value="final"
                  checked={daType === "final"}
                  onChange={() => setDaType("final")}
                  className="text-mint-500"
                />
                <span className="text-sm text-slate-700 dark:text-slate-300">Final</span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !portCallId}
            className="w-full rounded-lg bg-primary px-4 py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate DA"}
          </button>
        </div>
      </form>
    </div>
  );
}
