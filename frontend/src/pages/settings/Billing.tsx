import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router";
import { Check, CreditCard, Mail, TrendingUp } from "lucide-react";
import { toast } from "sonner";
import api, { ApiError } from "@/api/client";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";

export type BillingUsage = {
  users: number;
  vessels: number;
  das_this_month: number;
  ai_parses_this_month: number;
};

export type BillingLimits = {
  users: number | null;
  vessels: number | null;
  das_per_month: number | null;
  ai_parses_per_month: number | null;
};

export type BillingStatus = {
  plan: string;
  subscription_status: string;
  usage: BillingUsage;
  limits: BillingLimits;
};

const PLAN_LABELS: Record<string, string> = {
  starter: "Starter",
  professional: "Professional",
  enterprise: "Enterprise",
};

const SUPPORT_EMAIL = "support@portnomic.com";
const SUPPORT_SUBJECT = "ShipFlow - Plan change or cancellation";

const STATUS_VARIANTS: Record<
  string,
  "success" | "warning" | "destructive" | "outline"
> = {
  active: "success",
  trial: "outline",
  past_due: "warning",
  canceled: "destructive",
};

function formatLimit(value: number | null): string {
  return value === null ? "Unlimited" : value.toLocaleString();
}

function formatUsage(current: number, limit: number | null): string {
  if (limit === null) return `${current.toLocaleString()}`;
  return `${current.toLocaleString()} / ${limit.toLocaleString()}`;
}

const PURCHASABLE_PLANS = [
  { id: "starter" as const, name: "Starter", description: "Essential features for small teams" },
  { id: "professional" as const, name: "Professional", description: "Advanced features and AI parsing" },
] as const;

export function Billing() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [status, setStatus] = useState<BillingStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [purchasingPlan, setPurchasingPlan] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.get<BillingStatus>("/billing/status");
      setStatus(res.data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Failed to load billing status",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    const success = searchParams.get("success");
    const canceled = searchParams.get("canceled");

    if (success === "1") {
      toast.success("Subscription updated successfully.");
      fetchStatus();
      setSearchParams({}, { replace: true });
    } else if (canceled === "1") {
      toast.info("Checkout was canceled.");
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams, fetchStatus]);

  async function handlePurchase(plan: "starter" | "professional") {
    setPurchasingPlan(plan);
    const baseUrl = window.location.origin;
    const successUrl = `${baseUrl}/settings/billing?success=1`;
    const cancelUrl = `${baseUrl}/settings/billing?canceled=1`;

    try {
      const res = await api.post<{ url: string; form_data?: Record<string, string> }>(
        "/billing/create-checkout-session",
        {
          plan,
          success_url: successUrl,
          cancel_url: cancelUrl,
        },
      );
      if (res.data.form_data && res.data.url) {
        const form = document.createElement("form");
        form.method = "POST";
        form.action = res.data.url;
        for (const [k, v] of Object.entries(res.data.form_data)) {
          const input = document.createElement("input");
          input.type = "hidden";
          input.name = k;
          input.value = v;
          form.appendChild(input);
        }
        document.body.appendChild(form);
        form.submit();
      } else if (res.data.url) {
        window.location.href = res.data.url;
      } else {
        toast.error("No checkout URL returned.");
        setPurchasingPlan(null);
      }
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "Failed to start checkout",
      );
      setPurchasingPlan(null);
    }
  }

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-slate-100">Billing</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            View your plan, usage, and contact support for plan changes or
            cancellations.
          </p>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {status && (
        <>
          <Alert className="mb-4">
            <AlertDescription>
              Plan changes and cancellations are handled by our support team.{" "}
              <a
                href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(SUPPORT_SUBJECT)}`}
                className="underline hover:text-foreground"
              >
                Contact support
              </a>{" "}
              for assistance.
            </AlertDescription>
          </Alert>
          {/* Plan & status */}
          <Card className="mb-6">
            <CardHeader>
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <CardTitle className="flex items-center gap-3">
                    <CreditCard className="size-5" />
                    {PLAN_LABELS[status.plan] ?? status.plan}
                  </CardTitle>
                  <CardDescription>
                    Current subscription plan and status
                  </CardDescription>
                </div>
                <Badge
                  variant={
                    STATUS_VARIANTS[status.subscription_status] ?? "outline"
                  }
                >
                  {status.subscription_status.charAt(0).toUpperCase() +
                    status.subscription_status.slice(1)}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-3">
                <Button variant="outline" asChild>
                  <a
                    href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(SUPPORT_SUBJECT)}`}
                  >
                    <Mail className="size-4" />
                    Contact support
                  </a>
                </Button>
                {(status.plan === "professional" || status.plan === "enterprise") && (
                  <Button variant="outline" asChild>
                    <a
                      href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent("ShipFlow - Request downgrade")}`}
                    >
                      Request downgrade
                    </a>
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Purchase options */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Purchase options</CardTitle>
              <CardDescription>
                Choose a plan to purchase or upgrade. Enterprise plans require
                contacting support.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                {PURCHASABLE_PLANS.map((plan) => {
                  const isCurrentPlan =
                    status.plan === plan.id ||
                    (plan.id === "starter" &&
                      (status.plan === "trial" || !status.plan));
                  const isProOrEnterprise =
                    status.plan === "professional" || status.plan === "enterprise";
                  const canPurchaseViaCheckout =
                    plan.id === "professional"
                      ? !isProOrEnterprise
                      : !isProOrEnterprise && (status.plan === "trial" || !status.plan);
                  const needsContactSupport =
                    plan.id === "starter" && isProOrEnterprise;

                  return (
                    <div
                      key={plan.id}
                      className={`flex flex-col rounded-lg border p-4 ${
                        isCurrentPlan ? "border-primary bg-primary/5" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <h3 className="font-semibold">{plan.name}</h3>
                          <p className="text-sm text-muted-foreground">
                            {plan.description}
                          </p>
                        </div>
                        {isCurrentPlan && (
                          <Badge variant="outline" className="shrink-0">
                            <Check className="size-3" />
                            Current
                          </Badge>
                        )}
                      </div>
                      <div className="mt-4">
                        {isCurrentPlan ? (
                          <Button variant="outline" disabled size="sm">
                            Current plan
                          </Button>
                        ) : canPurchaseViaCheckout ? (
                          <Button
                            size="sm"
                            onClick={() => handlePurchase(plan.id)}
                            disabled={purchasingPlan !== null}
                          >
                            <TrendingUp className="size-4" />
                            {purchasingPlan === plan.id
                              ? "Redirecting…"
                              : plan.id === "professional"
                                ? "Upgrade to Professional"
                                : "Purchase Starter"}
                          </Button>
                        ) : needsContactSupport ? (
                          <Button variant="outline" asChild size="sm">
                            <a
                              href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent("ShipFlow - Request downgrade")}`}
                            >
                              Request downgrade
                            </a>
                          </Button>
                        ) : (
                          <Button variant="outline" asChild size="sm">
                            <a
                              href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent(`ShipFlow - ${plan.name} plan`)}`}
                            >
                              Contact support
                            </a>
                          </Button>
                        )}
                      </div>
                    </div>
                  );
                })}
                <div className="flex flex-col rounded-lg border border-dashed p-4">
                  <div>
                    <h3 className="font-semibold">Enterprise</h3>
                    <p className="text-sm text-muted-foreground">
                      Custom solutions for large agencies
                    </p>
                  </div>
                  <div className="mt-4">
                    <Button variant="outline" asChild size="sm">
                      <a
                        href={`mailto:${SUPPORT_EMAIL}?subject=${encodeURIComponent("ShipFlow - Enterprise plan")}`}
                      >
                        Contact support
                      </a>
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Usage table */}
          <Card>
            <CardHeader>
              <CardTitle>Usage this month</CardTitle>
              <CardDescription>
                Current usage against your plan limits
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-hidden rounded-lg border bg-muted/30">
                <table className="w-full text-left text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      <th className="px-4 py-3 font-medium text-muted-foreground">
                        Resource
                      </th>
                      <th className="px-4 py-3 font-medium text-muted-foreground">
                        Usage
                      </th>
                      <th className="px-4 py-3 font-medium text-muted-foreground">
                        Limit
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    <tr>
                      <td className="px-4 py-3 font-medium">Users</td>
                      <td className="px-4 py-3">
                        {formatUsage(
                          status.usage.users,
                          status.limits.users,
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {formatLimit(status.limits.users)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 font-medium">Vessels</td>
                      <td className="px-4 py-3">
                        {formatUsage(
                          status.usage.vessels,
                          status.limits.vessels,
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {formatLimit(status.limits.vessels)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 font-medium">
                        Disbursement Accounts (this month)
                      </td>
                      <td className="px-4 py-3">
                        {formatUsage(
                          status.usage.das_this_month,
                          status.limits.das_per_month,
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {formatLimit(status.limits.das_per_month)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-4 py-3 font-medium">
                        AI parses (this month)
                      </td>
                      <td className="px-4 py-3">
                        {formatUsage(
                          status.usage.ai_parses_this_month,
                          status.limits.ai_parses_per_month,
                        )}
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {formatLimit(status.limits.ai_parses_per_month)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
