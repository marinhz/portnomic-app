import { useState, useEffect } from "react";
import { Link } from "react-router";
import {
  LayoutDashboard,
  Ship,
  Anchor,
  Activity,
  FileText,
  ArrowRight,
  AlertCircle,
  CheckCircle,
  XCircle,
  Clock,
  Circle,
  Send,
} from "lucide-react";
import api, { ApiError } from "@/api/client";
import type {
  PaginatedResponse,
  VesselResponse,
  PortCallResponse,
  DAListResponse,
} from "@/api/types";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useAuth } from "@/auth/AuthContext";

const PORT_CALL_STATUS_VARIANT: Record<
  string,
  "info" | "success" | "warning" | "outline" | "destructive"
> = {
  planned: "info",
  arrived: "success",
  berthed: "warning",
  departed: "outline",
  cancelled: "destructive",
};

const DA_STATUS_VARIANT: Record<
  string,
  "secondary" | "warning" | "info" | "success"
> = {
  draft: "secondary",
  pending_approval: "warning",
  approved: "info",
  sent: "success",
};

export function Dashboard() {
  const { user } = useAuth();
  const [vesselCount, setVesselCount] = useState(0);
  const [portCallCount, setPortCallCount] = useState(0);
  const [activePortCallCount, setActivePortCallCount] = useState(0);
  const [daCount, setDaCount] = useState(0);
  const [recentVessels, setRecentVessels] = useState<VesselResponse[]>([]);
  const [recentPortCalls, setRecentPortCalls] = useState<PortCallResponse[]>([]);
  const [recentDAs, setRecentDAs] = useState<DAListResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hasDARead = user?.permissions.includes("da:read") ?? false;

  useEffect(() => {
    async function loadDashboard() {
      try {
        const promises: Promise<void>[] = [
          api
            .get<PaginatedResponse<VesselResponse>>("/vessels", {
              params: { page: 1, per_page: 3 },
            })
            .then((res) => {
              setVesselCount(res.data.meta.total);
              setRecentVessels(res.data.data);
            }),
          api
            .get<PaginatedResponse<PortCallResponse>>("/port-calls", {
              params: { page: 1, per_page: 3 },
            })
            .then((res) => {
              setPortCallCount(res.data.meta.total);
              setRecentPortCalls(res.data.data);
            }),
          api
            .get<PaginatedResponse<PortCallResponse>>("/port-calls", {
              params: { page: 1, per_page: 1, status: "arrived" },
            })
            .then((res) => {
              setActivePortCallCount(res.data.meta.total);
            }),
        ];

        if (hasDARead) {
          promises.push(
            api
              .get<PaginatedResponse<DAListResponse>>("/da", {
                params: { page: 1, per_page: 3 },
              })
              .then((res) => {
                setDaCount(res.data.meta.total);
                setRecentDAs(res.data.data);
              }),
          );
        }

        await Promise.all(promises);
      } catch (err) {
        setError(
          err instanceof ApiError ? err.message : "Failed to load dashboard",
        );
      } finally {
        setLoading(false);
      }
    }
    loadDashboard();
  }, [hasDARead]);

  if (loading) return <DashboardSkeleton hasDARead={hasDARead} />;
  if (error)
    return (
      <Alert variant="destructive">
        <AlertCircle className="size-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );

  return (
    <div className="min-h-0 space-y-6">
      <header>
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-mint-100 p-2 dark:bg-navy-800">
            <LayoutDashboard className="size-6 text-mint-500 dark:text-mint-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {user?.email
                ? `Welcome back, ${user.email.split("@")[0]}`
                : "Dashboard"}
            </h1>
            <p className="text-sm text-muted-foreground">
              Overview of your vessels, port calls, and disbursement accounts
            </p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <SummaryCard
          title="Total Vessels"
          value={vesselCount}
          link="/vessels"
          linkText="View all vessels"
          icon={<Ship className="size-6 text-mint-500 dark:text-mint-300" />}
        />
        <SummaryCard
          title="Total Port Calls"
          value={portCallCount}
          link="/port-calls"
          linkText="View all port calls"
          icon={<Anchor className="size-6 text-mint-500 dark:text-mint-300" />}
        />
        <SummaryCard
          title="Active Port Calls"
          value={activePortCallCount}
          link="/port-calls?status=arrived"
          linkText="View active"
          icon={<Activity className="size-6 text-mint-500 dark:text-mint-300" />}
        />
        {hasDARead ? (
          <SummaryCard
            title="Disbursement Accounts"
            value={daCount}
            link="/da"
            linkText="View all DAs"
            icon={<FileText className="size-6 text-mint-500 dark:text-mint-300" />}
          />
        ) : (
          <SummaryCard
            title="Recent Activity"
            value={recentVessels.length + recentPortCalls.length}
            icon={<Activity className="size-6 text-mint-500 dark:text-mint-300" />}
          />
        )}
      </div>

      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-2 lg:grid-rows-[auto_auto]">
        <Card className="flex flex-col lg:row-start-1 lg:col-start-1">
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Recent Vessels</CardTitle>
              <CardAction>
              <Button variant="link" className="h-auto p-0" asChild>
                <Link to="/vessels">
                  View all
                  <ArrowRight className="ml-1 size-4" />
                </Link>
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="overflow-visible">
            {recentVessels.length === 0 ? (
              <EmptyState
                icon={<Ship className="size-8 text-muted-foreground" />}
                title="No vessels yet"
                description="Add your first vessel to get started."
                action={
                  <Button variant="outline" size="sm" asChild>
                    <Link to="/vessels/new">Add vessel</Link>
                  </Button>
                }
              />
            ) : (
              <div className="space-y-3 pr-2">
                  {recentVessels.map((vessel) => (
                    <Link
                      key={vessel.id}
                      to={`/vessels/${vessel.id}`}
                      className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                    >
                      <div className="flex items-center gap-3">
                        <Ship className="size-5 text-muted-foreground" />
                        <div>
                          <p className="font-medium">{vessel.name}</p>
                          <p className="text-sm text-muted-foreground">
                            IMO: {vessel.imo ?? "N/A"}
                          </p>
                        </div>
                      </div>
                      <Badge variant="outline">{vessel.vessel_type ?? "—"}</Badge>
                    </Link>
                  ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="flex flex-col lg:row-start-1 lg:col-start-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Recent Port Calls</CardTitle>
              <CardAction>
                <Button variant="link" className="h-auto p-0" asChild>
                  <Link to="/port-calls">
                    View all
                    <ArrowRight className="ml-1 size-4" />
                  </Link>
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="overflow-visible">
              {recentPortCalls.length === 0 ? (
                <EmptyState
                  icon={<Anchor className="size-8 text-muted-foreground" />}
                  title="No port calls yet"
                  description="Create your first port call to get started."
                  action={
                    <Button variant="outline" size="sm" asChild>
                      <Link to="/port-calls/new">Add port call</Link>
                    </Button>
                  }
                />
              ) : (
                <div className="space-y-3 pr-2">
                    {recentPortCalls.map((pc) => (
                      <Link
                        key={pc.id}
                        to={`/port-calls/${pc.id}`}
                        className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-3">
                          <Anchor className="size-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium">Port Call</p>
                            <p className="text-sm text-muted-foreground">
                              {pc.eta
                                ? new Date(pc.eta).toLocaleDateString()
                                : "No ETA"}
                            </p>
                          </div>
                        </div>
                        <PortCallStatusBadge status={pc.status} />
                      </Link>
                    ))}
                </div>
              )}
          </CardContent>
        </Card>

        {hasDARead && (
          <Card className="flex flex-col lg:col-span-2 lg:row-start-2">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle>Recent Disbursement Accounts</CardTitle>
              <CardAction>
                <Button variant="link" className="h-auto p-0" asChild>
                  <Link to="/da">
                    View all
                    <ArrowRight className="ml-1 size-4" />
                  </Link>
                </Button>
              </CardAction>
            </CardHeader>
            <CardContent className="overflow-visible">
              {recentDAs.length === 0 ? (
                <EmptyState
                  icon={<FileText className="size-8 text-muted-foreground" />}
                  title="No disbursement accounts yet"
                  description="Create your first DA to get started."
                  action={
                    <Button variant="outline" size="sm" asChild>
                      <Link to="/da/generate">Create DA</Link>
                    </Button>
                  }
                />
              ) : (
                <div className="space-y-3 pr-2">
                    {recentDAs.map((da) => (
                      <Link
                        key={da.id}
                        to={`/da/${da.id}`}
                        className="flex items-center justify-between rounded-lg border border-border p-3 transition-colors hover:bg-muted/50"
                      >
                        <div className="flex items-center gap-3">
                          <FileText className="size-5 text-muted-foreground" />
                          <div>
                            <p className="font-medium capitalize">{da.type} DA</p>
                            <p className="text-sm text-muted-foreground">
                              v{da.version}
                            </p>
                          </div>
                          <DABadge status={da.status} />
                        </div>
                        <span className="text-sm text-muted-foreground">
                          {new Date(da.created_at).toLocaleDateString()}
                        </span>
                      </Link>
                    ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  link,
  linkText,
  icon,
}: {
  title: string;
  value: number;
  link?: string;
  linkText?: string;
  icon: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="rounded-lg bg-mint-100 p-2 dark:bg-navy-800">{icon}</div>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-bold">{value}</p>
        {link && linkText && (
          <Button variant="link" className="mt-2 h-auto p-0" asChild>
            <Link to={link}>
              {linkText}
              <ArrowRight className="ml-1 size-4" />
            </Link>
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="rounded-full bg-muted p-4">
        {icon}
      </div>
      <p className="mt-4 text-sm font-medium text-muted-foreground">{title}</p>
      <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

const PORT_CALL_STATUS_ICON: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  planned: Clock,
  arrived: CheckCircle,
  berthed: Anchor,
  departed: Ship,
  cancelled: XCircle,
};

function PortCallStatusBadge({ status }: { status: string }) {
  const key = status.toLowerCase();
  const variant = PORT_CALL_STATUS_VARIANT[key] ?? "outline";
  const Icon = PORT_CALL_STATUS_ICON[key] ?? Anchor;
  return (
    <Badge variant={variant}>
      <Icon className="size-4" />
      {status}
    </Badge>
  );
}

const DA_STATUS_ICON: Record<
  string,
  React.ComponentType<{ className?: string }>
> = {
  draft: Circle,
  pending_approval: AlertCircle,
  approved: CheckCircle,
  sent: Send,
};

function DABadge({ status }: { status: string }) {
  const variant = DA_STATUS_VARIANT[status] ?? "secondary";
  const Icon = DA_STATUS_ICON[status] ?? FileText;
  return (
    <Badge variant={variant}>
      <Icon className="size-4" />
      {status.replace("_", " ")}
    </Badge>
  );
}

function DashboardSkeleton({ hasDARead }: { hasDARead: boolean }) {
  return (
    <div className="space-y-6">
      <header>
        <div className="flex items-center gap-3">
          <Skeleton className="size-10 rounded-lg" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-64" />
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i}>
            <CardHeader className="space-y-0 pb-2">
              <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="size-9 rounded-lg" />
              </div>
            </CardHeader>
            <CardContent>
              <Skeleton className="h-9 w-16" />
              <Skeleton className="mt-2 h-4 w-28" />
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2 lg:grid-rows-[auto_auto]">
        <Card className="lg:row-start-1 lg:col-start-1">
          <CardHeader>
            <Skeleton className="h-5 w-32" />
            <Skeleton className="h-4 w-16" />
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </CardContent>
        </Card>
        <Card className="lg:row-start-1 lg:col-start-2">
          <CardHeader>
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-4 w-16" />
          </CardHeader>
          <CardContent className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-16 w-full rounded-lg" />
            ))}
          </CardContent>
        </Card>

        {hasDARead && (
          <Card className="lg:col-span-2 lg:row-start-2">
            <CardHeader>
              <Skeleton className="h-5 w-48" />
              <Skeleton className="h-4 w-16" />
            </CardHeader>
            <CardContent className="space-y-3">
              {[1, 2].map((i) => (
                <Skeleton key={i} className="h-16 w-full rounded-lg" />
              ))}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
