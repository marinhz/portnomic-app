import { Link } from "react-router";
import type { LucideIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export type PlanUpgradeGateProps = {
  /** Feature name for context (e.g. "AI Settings") */
  featureName: string;
  /** Required plans (e.g. "Professional and Enterprise") */
  requiredPlans: string;
  /** Main message - use API message when available */
  message: string;
  /** Short description of what the user gets */
  description: string;
  /** Icon component (e.g. Sparkles, Lock, Zap) */
  icon: LucideIcon;
  /** Billing/plans destination path */
  billingPath?: string;
  /** Optional "View plans" link - shown as secondary */
  showViewPlans?: boolean;
  /** Full-page marketing layout (no surrounding chrome) */
  variant?: "card" | "fullPage";
  className?: string;
};

const DEFAULT_BILLING_PATH = "/settings/billing";

/**
 * Reusable upgrade gate card for plan-gated features.
 * Shows a prominent, polished message when a user needs to upgrade.
 */
export function PlanUpgradeGate({
  featureName,
  requiredPlans,
  message,
  description,
  icon: Icon,
  billingPath = DEFAULT_BILLING_PATH,
  showViewPlans = true,
  variant = "card",
  className,
}: PlanUpgradeGateProps) {
  const isFullPage = variant === "fullPage";

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center px-4",
        isFullPage
          ? "min-h-[60vh] py-20 bg-gradient-to-b from-mint-50/80 to-background dark:from-navy-900/50 dark:to-background rounded-xl"
          : "py-16",
        className
      )}
    >
      <div className={cn("w-full", isFullPage ? "max-w-lg" : "max-w-md")}>
        <Card
          className={cn(
            "border-2 border-mint-200 dark:border-mint-500/50",
            "bg-white/90 dark:bg-navy-800/80 backdrop-blur-sm",
            "shadow-xl",
            isFullPage && "py-2"
          )}
          aria-label={`${featureName} — upgrade to ${requiredPlans} required`}
        >
          <CardHeader className={cn(isFullPage && "space-y-6")}>
            <div className="flex flex-col sm:flex-row items-center sm:items-start gap-6 text-center sm:text-left">
              <div
                className={cn(
                  "shrink-0 rounded-2xl p-4",
                  "bg-mint-100 dark:bg-navy-700",
                  "text-mint-600 dark:text-mint-400"
                )}
              >
                <Icon className={cn(isFullPage ? "size-12" : "size-8")} aria-hidden />
              </div>
              <div className="min-w-0 space-y-2 flex-1">
                <CardTitle
                  className={cn(
                    "leading-snug text-foreground",
                    isFullPage ? "text-xl sm:text-2xl" : "text-lg"
                  )}
                >
                  {message}
                </CardTitle>
                <CardDescription
                  className={cn(isFullPage ? "text-base" : "text-sm")}
                >
                  {description}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-3 justify-center sm:justify-start">
            <Button asChild size={isFullPage ? "lg" : "default"}>
              <Link to={billingPath}>Upgrade plan</Link>
            </Button>
            {showViewPlans && (
              <Button variant="outline" asChild size={isFullPage ? "lg" : "default"}>
                <Link to={billingPath}>View plans</Link>
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
