import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router";
import {
  Mail,
  Inbox,
  Server,
  RefreshCw,
  Trash2,
  CheckCircle,
  XCircle,
  AlertCircle,
  MinusCircle,
  Cable,
  Info,
} from "lucide-react";

const SHOW_OUTLOOK_CONNECT =
  (import.meta as { env?: { VITE_SHOW_OUTLOOK_CONNECT?: string } }).env
    ?.VITE_SHOW_OUTLOOK_CONNECT === "true";
import { toast } from "sonner";
import api, { ApiError } from "@/api/client";
import type {
  SingleResponse,
  MailConnectionResponse,
  ImapConnectionCreate,
} from "@/api/types";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

const PROVIDER_LABELS: Record<string, string> = {
  gmail: "Gmail",
  outlook: "Outlook / Microsoft 365",
  imap: "IMAP",
};

function StatusBadge({ status, title }: { status: string; title?: string }) {
  const { variant, Icon } =
    status === "connected"
      ? { variant: "success" as const, Icon: CheckCircle }
      : status === "error"
        ? { variant: "destructive" as const, Icon: XCircle }
        : status === "syncing" || status === "pending"
          ? { variant: "warning" as const, Icon: AlertCircle }
          : { variant: "outline" as const, Icon: MinusCircle };
  return (
    <Badge variant={variant} title={title}>
      <Icon className="size-4 shrink-0" />
      {status}
    </Badge>
  );
}

export function IntegrationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [connections, setConnections] = useState<MailConnectionResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [showImapForm, setShowImapForm] = useState(false);
  const [imapForm, setImapForm] = useState<ImapConnectionCreate>({
    imap_host: "",
    imap_port: 993,
    imap_user: "",
    imap_password: "",
  });
  const [imapSubmitting, setImapSubmitting] = useState(false);
  const [imapFormError, setImapFormError] = useState<string | null>(null);
  const [imapTesting, setImapTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);

  const fetchConnections = useCallback(async () => {
    try {
      const res = await api.get<SingleResponse<MailConnectionResponse[]>>(
        "/integrations/email",
      );
      setConnections(res.data.data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to load connections",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConnections();
  }, [fetchConnections]);

  useEffect(() => {
    const emailParam = searchParams.get("email");
    const errorParam = searchParams.get("error");
    const provider = searchParams.get("provider");

    if (emailParam === "connected") {
      toast.success(
        `${PROVIDER_LABELS[provider ?? ""] ?? "Email"} connected successfully!`,
      );
      fetchConnections();
      setSearchParams({}, { replace: true });
    } else if (errorParam) {
      toast.error(`Connection failed: ${errorParam}`);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, fetchConnections]);

  async function handleConnect(provider: "gmail" | "outlook") {
    try {
      const res = await api.get<{ url: string }>(
        `/integrations/email/connect?provider=${provider}`,
      );
      window.location.href = res.data.url;
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Failed to start OAuth flow",
      );
    }
  }

  async function handleDelete(id: string) {
    try {
      await api.delete(`/integrations/email/${id}`);
      setConnections((prev) => prev.filter((c) => c.id !== id));
      toast.success("Connection removed.");
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Failed to disconnect",
      );
    } finally {
      setConfirmDeleteId(null);
    }
  }

  async function handleSyncNow(full = false) {
    setSyncing(true);
    const toastId = toast.loading("Syncing…");
    try {
      const res = await api.post<{ ingested: number }>(
        "/integrations/email/sync",
        null,
        { params: full ? { full: "1" } : {} },
      );
      if (res.data.ingested > 0) {
        toast.success(
          `Synced ${res.data.ingested} new email(s). Check Emails page.`,
          { id: toastId },
        );
      } else {
        toast.info("Sync complete. No new emails.", { id: toastId });
      }
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Sync failed",
        { id: toastId },
      );
    } finally {
      setSyncing(false);
    }
  }

  async function handleTestConnection(e: React.MouseEvent<HTMLButtonElement>) {
    e.preventDefault();
    setImapFormError(null);
    setImapTesting(true);
    try {
      const res = await api.post<{ ok: boolean; error?: string }>(
        "/integrations/email/imap/test",
        imapForm,
      );
      if (res.data.ok) {
        toast.success("Connection successful.");
      } else {
        setImapFormError(res.data.error ?? "Connection failed.");
      }
    } catch (err) {
      setImapFormError(
        err instanceof ApiError ? err.message : "Test connection failed.",
      );
    } finally {
      setImapTesting(false);
    }
  }

  async function handleImapSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setImapFormError(null);
    setImapSubmitting(true);
    try {
      await api.post<SingleResponse<MailConnectionResponse>>(
        "/integrations/email/imap",
        imapForm,
      );
      setShowImapForm(false);
      setImapForm({
        imap_host: "",
        imap_port: 993,
        imap_user: "",
        imap_password: "",
      });
      toast.success("IMAP connection added.");
      fetchConnections();
    } catch (err) {
      const message =
        err instanceof ApiError ? err.message : "Failed to add IMAP connection";
      setImapFormError(message);
      // Form values preserved; user can correct and retry (Task 6.12: error in Alert, not just toast)
    } finally {
      setImapSubmitting(false);
    }
  }

  const connToDelete = connections.find((c) => c.id === confirmDeleteId);

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">
            Email Integrations
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Connect mailboxes for automatic email ingest and AI parsing.
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Sync now + Connect buttons */}
      <div className="mb-6 flex flex-wrap gap-6">
        <Button
          onClick={() => handleSyncNow(false)}
          disabled={syncing || connections.length === 0}
        >
          <RefreshCw
            className={`size-4 ${syncing ? "animate-spin" : ""}`}
          />
          {syncing ? "Syncing…" : "Sync now"}
        </Button>
        <Button
          variant="outline"
          onClick={() => handleSyncNow(true)}
          disabled={syncing || connections.length === 0}
          title="Reset sync state and re-fetch recent emails from INBOX"
        >
          Full sync
        </Button>
        <div className="inline-flex items-center gap-1.5">
          <Button variant="outline" onClick={() => handleConnect("gmail")}>
            <Mail className="size-4" />
            Connect Gmail
          </Button>
          <Tooltip>
            <TooltipTrigger asChild>
              <span
                className="inline-flex cursor-help text-muted-foreground hover:text-foreground"
                aria-label="Gmail connection info"
              >
                <Info className="size-4" />
              </span>
            </TooltipTrigger>
            <TooltipContent side="bottom" className="max-w-xs">
              Read-only access for vessel email parsing. Your data is encrypted
              and never shared. Verification with Google in progress for a
              trusted experience.
            </TooltipContent>
          </Tooltip>
        </div>
        {SHOW_OUTLOOK_CONNECT && (
          <Button variant="outline" onClick={() => handleConnect("outlook")}>
            <Inbox className="size-4" />
            Connect Outlook
          </Button>
        )}
        <Button
          variant="outline"
          onClick={() => setShowImapForm((v) => !v)}
        >
          <Server className="size-4" />
          {showImapForm ? "Cancel IMAP" : "Add IMAP"}
        </Button>
      </div>

      {/* Gmail privacy note */}
      <Alert className="mb-6">
        <Info className="size-4" />
        <AlertDescription>
          <strong>Gmail:</strong> We use read-only access to parse
          vessel-related emails. Your data is encrypted and never shared.
        </AlertDescription>
      </Alert>

      {/* IMAP form */}
      {showImapForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add IMAP Connection</CardTitle>
          </CardHeader>
          <CardContent>
            {imapFormError && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{imapFormError}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleImapSubmit} className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="imap_host">IMAP Host</Label>
                <Input
                  id="imap_host"
                  type="text"
                  required
                  value={imapForm.imap_host}
                  onChange={(e) => {
                    setImapForm((p) => ({ ...p, imap_host: e.target.value }));
                    setImapFormError(null);
                  }}
                  placeholder="imap.example.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="imap_port">Port</Label>
                <Input
                  id="imap_port"
                  type="number"
                  required
                  value={imapForm.imap_port}
                  onChange={(e) => {
                    setImapForm((p) => ({
                      ...p,
                      imap_port: Number(e.target.value),
                    }));
                    setImapFormError(null);
                  }}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="imap_user">Username</Label>
                <Input
                  id="imap_user"
                  type="text"
                  required
                  value={imapForm.imap_user}
                  onChange={(e) => {
                    setImapForm((p) => ({ ...p, imap_user: e.target.value }));
                    setImapFormError(null);
                  }}
                  placeholder="user@example.com"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="imap_password">Password</Label>
                <Input
                  id="imap_password"
                  type="password"
                  required
                  value={imapForm.imap_password}
                  onChange={(e) => {
                    setImapForm((p) => ({
                      ...p,
                      imap_password: e.target.value,
                    }));
                    setImapFormError(null);
                  }}
                />
              </div>
              <div className="flex flex-wrap gap-2 justify-end sm:col-span-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={handleTestConnection}
                  disabled={imapTesting || imapSubmitting}
                >
                  <Cable className="size-4" />
                  {imapTesting ? "Testing..." : "Test connection"}
                </Button>
                <Button type="submit" disabled={imapSubmitting}>
                  {imapSubmitting ? "Adding..." : "Add IMAP Connection"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Connections table */}
      {connections.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-sm text-muted-foreground">
            No email connections yet. Connect Gmail, Outlook, or IMAP above.
          </CardContent>
        </Card>
      ) : (
        <div className="overflow-hidden rounded-lg border bg-card shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="border-b bg-muted/50">
              <tr>
                <th className="px-4 py-3 font-medium text-muted-foreground">
                  Provider
                </th>
                <th className="px-4 py-3 font-medium text-muted-foreground">
                  Email
                </th>
                <th className="px-4 py-3 font-medium text-muted-foreground">
                  Status
                </th>
                <th className="px-4 py-3 font-medium text-muted-foreground">
                  Last Sync
                </th>
                <th className="px-4 py-3 font-medium text-muted-foreground">
                  Connected
                </th>
                <th className="px-4 py-3 font-medium text-muted-foreground" />
              </tr>
            </thead>
            <tbody className="divide-y">
              {connections.map((conn) => (
                <tr key={conn.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">
                    {PROVIDER_LABELS[conn.provider] ?? conn.provider}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {conn.display_email ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge
                      status={conn.status}
                      title={conn.error_message ?? undefined}
                    />
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {conn.last_sync_at
                      ? new Date(conn.last_sync_at).toLocaleString()
                      : "Never"}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {new Date(conn.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                      onClick={() => setConfirmDeleteId(conn.id)}
                    >
                      <Trash2 className="size-4" />
                      Disconnect
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete confirmation dialog */}
      <Dialog
        open={!!confirmDeleteId}
        onOpenChange={(open) => !open && setConfirmDeleteId(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Disconnect email?</DialogTitle>
            <DialogDescription>
              {connToDelete && (
                <>
                  This will remove the{" "}
                  <strong>
                    {PROVIDER_LABELS[connToDelete.provider] ?? connToDelete.provider}{" "}
                    ({connToDelete.display_email ?? "—"})
                  </strong>{" "}
                  connection. You can reconnect later.
                </>
              )}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setConfirmDeleteId(null)}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => confirmDeleteId && handleDelete(confirmDeleteId)}
            >
              Disconnect
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
