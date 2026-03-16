import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  SingleResponse,
  VesselResponse,
  PortResponse,
  PortCallResponse,
  UserResponse,
} from "@/api/types";
import { SearchableSelect, type SearchableOption } from "@/components/SearchableSelect";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

const STEPS = [
  { id: 1, title: "Vessel", description: "Select the vessel" },
  { id: 2, title: "Port", description: "Select the port" },
  { id: 3, title: "ETA / ETD / Agent", description: "Enter dates and agent" },
] as const;

export function PortCallWizard() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialVesselId = searchParams.get("vessel_id") ?? "";

  const [step, setStep] = useState(1);
  const [vesselId, setVesselId] = useState(initialVesselId);
  const [portId, setPortId] = useState("");
  const [eta, setEta] = useState("");
  const [etd, setEtd] = useState("");
  const [agentAssignedId, setAgentAssignedId] = useState<string>("");

  const [vessels, setVessels] = useState<VesselResponse[]>([]);
  const [ports, setPorts] = useState<PortResponse[]>([]);
  const [users, setUsers] = useState<UserResponse[]>([]);
  const [portSearchLoading, setPortSearchLoading] = useState(false);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const vesselOptions: SearchableOption[] = vessels.map((v) => ({
    id: v.id,
    label: `${v.name}${v.imo ? ` (IMO: ${v.imo})` : ""}`,
  }));

  const portOptions: SearchableOption[] = ports.map((p) => ({
    id: p.id,
    label: `${p.name} (${p.code})`,
  }));

  const userOptions: SearchableOption[] = users.map((u) => ({
    id: u.id,
    label: u.email,
  }));

  const fetchVessels = useCallback(async () => {
    const res = await api.get<PaginatedResponse<VesselResponse>>("/vessels", {
      params: { per_page: 500 },
    });
    setVessels(res.data.data);
  }, []);

  const fetchPorts = useCallback(async (search?: string) => {
    setPortSearchLoading(true);
    try {
      const res = await api.get<PaginatedResponse<PortResponse>>("/ports", {
        params: { per_page: 50, search: search ?? "" },
      });
      setPorts(res.data.data);
    } finally {
      setPortSearchLoading(false);
    }
  }, []);

  const fetchUsers = useCallback(async () => {
    try {
      const res = await api.get<PaginatedResponse<UserResponse>>("/admin/users", {
        params: { per_page: 100 },
      });
      setUsers(res.data.data);
    } catch {
      setUsers([]);
    }
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        await Promise.all([fetchVessels(), fetchPorts(""), fetchUsers()]);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load data",
        );
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [fetchVessels, fetchPorts, fetchUsers]);

  const portSearchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const handlePortSearch = useCallback(
    (query: string) => {
      if (portSearchTimeout.current) clearTimeout(portSearchTimeout.current);
      portSearchTimeout.current = setTimeout(() => {
        fetchPorts(query);
        portSearchTimeout.current = null;
      }, 200);
    },
    [fetchPorts],
  );

  const canProceedStep1 = !!vesselId;
  const canProceedStep2 = !!portId;
  const canSubmit = vesselId && portId;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    const payload = {
      vessel_id: vesselId,
      port_id: portId,
      eta: eta || undefined,
      etd: etd || undefined,
      status: "scheduled",
      agent_assigned_id: agentAssignedId || null,
      source: "manual" as const,
    };

    try {
      const res = await api.post<SingleResponse<PortCallResponse>>(
        "/port-calls",
        payload,
      );
      navigate(`/port-calls/${res.data.data.id}`);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to create port call",
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold text-slate-800 dark:text-slate-100">
        New Port Call
      </h1>

      <div className="mb-8">
        <nav aria-label="Progress">
          <ol className="flex items-center gap-2">
            {STEPS.map((s, i) => (
              <li key={s.id} className="flex items-center gap-2">
                <div
                  className={cn(
                    "flex size-9 items-center justify-center rounded-full text-sm font-medium",
                    step >= s.id
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  {s.id}
                </div>
                <span
                  className={cn(
                    "text-sm font-medium",
                    step >= s.id
                      ? "text-foreground"
                      : "text-muted-foreground",
                  )}
                >
                  {s.title}
                </span>
                {i < STEPS.length - 1 && (
                  <span className="mx-1 text-muted-foreground">→</span>
                )}
              </li>
            ))}
          </ol>
        </nav>
      </div>

      <Card className="mx-auto max-w-2xl">
        <CardHeader>
          <CardTitle>{STEPS[step - 1].title}</CardTitle>
          <CardDescription>{STEPS[step - 1].description}</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              {error}
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="vessel">Vessel</Label>
                <SearchableSelect
                  value={vesselId}
                  onSelect={setVesselId}
                  options={vesselOptions}
                  searchPlaceholder="Search by name or IMO..."
                  required
                  aria-label="Select vessel"
                />
              </div>
              <div className="flex justify-end">
                <Button
                  type="button"
                  onClick={() => setStep(2)}
                  disabled={!canProceedStep1}
                >
                  Next
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="port">Port</Label>
                <SearchableSelect
                  value={portId}
                  onSelect={setPortId}
                  options={portOptions}
                  onSearch={handlePortSearch}
                  loading={portSearchLoading}
                  filterMode="server"
                  searchPlaceholder="Search by name, code, or country..."
                  required
                  aria-label="Select port"
                />
              </div>
              <div className="flex justify-between">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                >
                  Back
                </Button>
                <Button
                  type="button"
                  onClick={() => setStep(3)}
                  disabled={!canProceedStep2}
                >
                  Next
                </Button>
              </div>
            </div>
          )}

          {step === 3 && (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="eta">ETA</Label>
                  <Input
                    id="eta"
                    type="date"
                    value={eta}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setEta(e.target.value)
                    }
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="etd">ETD</Label>
                  <Input
                    id="etd"
                    type="date"
                    value={etd}
                    onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                      setEtd(e.target.value)
                    }
                  />
                </div>
              </div>

              {userOptions.length > 0 && (
                <div className="space-y-2">
                  <Label htmlFor="agent">Agent Assigned</Label>
                  <SearchableSelect
                    value={agentAssignedId}
                    onSelect={setAgentAssignedId}
                    options={userOptions}
                    searchPlaceholder="Search by email..."
                    aria-label="Select agent"
                  />
                </div>
              )}

              <div className="flex justify-between pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(2)}
                >
                  Back
                </Button>
                <Button type="submit" disabled={submitting || !canSubmit}>
                  {submitting ? "Creating..." : "Create Port Call"}
                </Button>
              </div>
            </form>
          )}
        </CardContent>
      </Card>

      <div className="mt-4">
        <Button
          variant="ghost"
          onClick={() => navigate("/port-calls")}
          className="text-muted-foreground"
        >
          Cancel
        </Button>
      </div>
    </div>
  );
}
