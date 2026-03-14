import { Link } from "react-router";
import { ShieldCheck, FileText } from "lucide-react";
import { useAuth } from "@/auth/AuthContext";
import { PlanUpgradeGate } from "@/components/PlanUpgradeGate";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";

/**
 * Leakage Detector page — AI-powered expense audit.
 * Feature-gated to Professional and Enterprise plans.
 * Users with da:read can access DAs to review anomalies.
 */
export function LeakageDetectorPage() {
  const { user } = useAuth();
  const leakageDetectorEnabled = user?.leakage_detector_enabled ?? false;
  const isPlatformAdmin = user?.is_platform_admin ?? false;
  const hasDARead = user?.permissions.includes("da:read") ?? false;

  const hasAccess = leakageDetectorEnabled || isPlatformAdmin;

  if (!hasAccess) {
    return (
      <div className="container max-w-4xl py-8">
        <PlanUpgradeGate
          featureName="Leakage Detector"
          requiredPlans="Professional and Enterprise"
          message="Leakage Detector is available on Professional and Enterprise plans."
          description="Automatically cross-reference vendor invoices against operational data to identify overbilling, duplicate charges, or tariff misapplications."
          icon={ShieldCheck}
          billingPath="/settings/billing"
          showViewPlans={true}
          variant="fullPage"
        />
      </div>
    );
  }

  return (
    <div className="container max-w-4xl py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight text-navy-950 dark:text-slate-100">
          Leakage Detector
        </h1>
        <p className="mt-1 text-slate-600 dark:text-slate-400">
          AI-powered expense audit — cross-reference invoices against operational
          data to catch overbilling and discrepancies.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-1 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-mint-100 p-2 dark:bg-navy-800">
                <ShieldCheck className="size-6 text-mint-600 dark:text-mint-400" />
              </div>
              <div>
                <CardTitle>How it works</CardTitle>
                <CardDescription>
                  When financial documents are parsed, the system automatically
                  compares line items against Port Call data and audit logs.
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
            <p>
              <strong>LD-001</strong> — Temporal validation (service date vs.
              vessel stay)
            </p>
            <p>
              <strong>LD-002</strong> — Duplicate detection (identical
              services/amounts)
            </p>
            <p>
              <strong>LD-003</strong> — Tariff shift audit (weekend/holiday rates)
            </p>
            <p>
              <strong>LD-004</strong> — Quantity variance (invoiced vs. noon
              reports)
            </p>
          </CardContent>
        </Card>

        {hasDARead && (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="rounded-lg bg-mint-100 p-2 dark:bg-navy-800">
                  <FileText className="size-6 text-mint-600 dark:text-mint-400" />
                </div>
                <div>
                  <CardTitle>Review DAs</CardTitle>
                  <CardDescription>
                    Open Disbursement Accounts to see flagged line items and
                    anomaly details.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Button asChild>
                <Link to="/da">View Disbursement Accounts</Link>
              </Button>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
