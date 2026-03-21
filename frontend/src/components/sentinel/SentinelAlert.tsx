import * as React from "react";
import { Link } from "react-router";
import { AlertTriangle } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import type { DiscrepancyResponse } from "@/api/types";

/** Severity-based accent styling for SentinelAlert card */
const SEVERITY_STYLES: Record<
  string,
  { accent: string; icon: string }
> = {
  high: {
    accent:
      "border-l-4 border-l-red-500 dark:border-l-red-500 bg-red-50/50 dark:bg-red-950/20",
    icon: "text-red-600 dark:text-red-400",
  },
  medium: {
    accent:
      "border-l-4 border-l-amber-500 dark:border-l-amber-500 bg-amber-50/50 dark:bg-amber-950/20",
    icon: "text-amber-600 dark:text-amber-400",
  },
  low: {
    accent:
      "border-l-4 border-l-blue-500 dark:border-l-blue-500 bg-blue-50/50 dark:bg-blue-950/20",
    icon: "text-blue-600 dark:text-blue-400",
  },
};

const DEFAULT_SEVERITY_STYLE = {
  accent:
    "border-l-4 border-l-slate-500 dark:border-l-slate-500 bg-slate-50/50 dark:bg-slate-900/50",
  icon: "text-slate-600 dark:text-slate-400",
};

function countBySeverity(discrepancies: DiscrepancyResponse[]): Record<string, number> {
  const counts: Record<string, number> = {};
  for (const d of discrepancies) {
    const s = (d.severity || "low").toLowerCase();
    counts[s] = (counts[s] ?? 0) + 1;
  }
  return counts;
}

function formatSummary(counts: Record<string, number>): string {
  const high = counts.high ?? 0;
  const medium = counts.medium ?? 0;
  const low = counts.low ?? 0;
  const parts: string[] = [];
  if (high > 0) parts.push(`${high} high-risk`);
  if (medium > 0) parts.push(`${medium} potential errors`);
  if (low > 0) parts.push(`${low} informational`);
  if (parts.length === 0) return "Discrepancies detected";
  return parts.join(", ");
}

function highestSeverity(counts: Record<string, number>): string {
  if ((counts.high ?? 0) > 0) return "high";
  if ((counts.medium ?? 0) > 0) return "medium";
  return "low";
}

export interface SentinelAlertProps {
  discrepancies: DiscrepancyResponse[];
  portCallId: string;
  onDismiss?: () => void;
  onViewDetails?: () => void;
  className?: string;
}

/** High-visibility Sentinel discrepancy alert card for Port Call dashboard. */
export function SentinelAlert({
  discrepancies,
  portCallId,
  onDismiss,
  onViewDetails,
  className,
}: SentinelAlertProps) {
  if (discrepancies.length === 0) return null;

  const counts = countBySeverity(discrepancies);
  const severity = highestSeverity(counts);
  const styles = SEVERITY_STYLES[severity] ?? DEFAULT_SEVERITY_STYLE;

  return (
    <Card
      role="alert"
      aria-live="polite"
      aria-label="Sentinel operational gap alerts"
      className={cn(styles.accent, className)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle
            className={cn("size-5 shrink-0", styles.icon)}
            aria-hidden
          />
          <h3 className="text-base font-semibold text-slate-800 dark:text-slate-100">
            Sentinel Alerts
          </h3>
        </div>
      </CardHeader>
      <CardContent className="space-y-2 pt-0">
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {formatSummary(counts)}
        </p>
        <div className="flex flex-wrap gap-2">
          {(counts.high ?? 0) > 0 && (
            <span className="rounded-full bg-red-200 px-2 py-0.5 text-xs font-medium text-red-800 dark:bg-red-900/50 dark:text-red-300">
              {counts.high} high
            </span>
          )}
          {(counts.medium ?? 0) > 0 && (
            <span className="rounded-full bg-amber-200 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
              {counts.medium} medium
            </span>
          )}
          {(counts.low ?? 0) > 0 && (
            <span className="rounded-full bg-blue-200 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/50 dark:text-blue-300">
              {counts.low} low
            </span>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex flex-wrap gap-2 pt-0">
        <Button asChild size="sm" variant="default">
          <Link to={`/port-calls/${portCallId}/audit`}>
            View audit details
          </Link>
        </Button>
        {onDismiss && (
          <Button
            size="sm"
            variant="ghost"
            onClick={onDismiss}
            aria-label="Dismiss Sentinel alerts"
          >
            Dismiss
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
