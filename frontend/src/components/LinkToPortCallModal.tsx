import { useState, useEffect, useCallback } from "react";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  PortCallResponse,
  VesselResponse,
  PortResponse,
} from "@/api/types";
import { SearchableSelect, type SearchableOption } from "@/components/SearchableSelect";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

type LinkToPortCallModalProps = {
  emailId: string;
  open: boolean;
  onClose: () => void;
  onLinked: () => void;
};

export function LinkToPortCallModal({
  emailId,
  open,
  onClose,
  onLinked,
}: LinkToPortCallModalProps) {
  const [portCalls, setPortCalls] = useState<PortCallResponse[]>([]);
  const [vessels, setVessels] = useState<VesselResponse[]>([]);
  const [ports, setPorts] = useState<PortResponse[]>([]);
  const [selectedPortCallId, setSelectedPortCallId] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [pcRes, vRes, pRes] = await Promise.all([
        api.get<PaginatedResponse<PortCallResponse>>("/port-calls", {
          params: { per_page: 100 },
        }),
        api.get<PaginatedResponse<VesselResponse>>("/vessels", {
          params: { per_page: 500 },
        }),
        api.get<PaginatedResponse<PortResponse>>("/ports", {
          params: { per_page: 200 },
        }),
      ]);
      setPortCalls(pcRes.data.data);
      setVessels(vRes.data.data);
      setPorts(pRes.data.data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      setSelectedPortCallId("");
      setError(null);
      fetchData();
    }
  }, [open, fetchData]);

  const vesselMap = Object.fromEntries(vessels.map((v) => [v.id, v]));
  const portMap = Object.fromEntries(ports.map((p) => [p.id, p]));

  const portCallOptions: SearchableOption[] = portCalls.map((pc) => {
    const vessel = vesselMap[pc.vessel_id];
    const port = portMap[pc.port_id];
    const vesselName = vessel?.name ?? pc.vessel_id.slice(0, 8);
    const portName = port?.name ?? port?.code ?? pc.port_id.slice(0, 8);
    const etaStr = pc.eta
      ? new Date(pc.eta).toLocaleDateString()
      : "No ETA";
    return {
      id: pc.id,
      label: `${vesselName} – ${portName} (${etaStr})`,
    };
  });

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!selectedPortCallId) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.patch(`/emails/${emailId}`, {
        port_call_id: selectedPortCallId,
      });
      onLinked();
      onClose();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to link email");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Link to Port Call</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="space-y-2">
            <label
              htmlFor="port-call-select"
              className="text-sm font-medium text-foreground"
            >
              Select Port Call
            </label>
            <SearchableSelect
              value={selectedPortCallId}
              onSelect={setSelectedPortCallId}
              options={portCallOptions}
              searchPlaceholder="Search by vessel or port..."
              loading={loading}
              required
              aria-label="Port call"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" disabled={!selectedPortCallId || submitting}>
              {submitting ? "Linking..." : "Link"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
