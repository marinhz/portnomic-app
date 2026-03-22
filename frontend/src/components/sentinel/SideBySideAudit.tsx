import { useState, Fragment } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

import { cn } from "@/lib/utils";
import type { DiscrepancyResponse } from "@/api/types";

/** Mapped row data from raw_evidence for display in three columns. */
export type AuditRowData = {
  vendorClaim: string;
  operationalReality: string;
  variance: string;
  isHighRisk: boolean;
};

/**
 * Extract vendor claim, operational reality, and variance from raw_evidence
 * based on Sentinel rule (S-001, S-002, S-003).
 */
function extractRowData(
  discrepancy: DiscrepancyResponse
): AuditRowData {
  const raw = discrepancy.raw_evidence ?? {};
  const severity = (discrepancy.severity ?? "low").toLowerCase();
  const isHighRisk = severity === "high";

  // S-001: Temporal Tug/Pilot Audit
  if (discrepancy.rule_id === "S-001") {
    const daHours = raw.da_hours as number | undefined;
    const sofHours = raw.sof_hours as number | undefined;
    const sofEvents = raw.sof_events as number | undefined;
    const buffer = (raw.buffer_hours as number) ?? 0.5;

    if (sofEvents === 0 || sofHours === undefined) {
      return {
        vendorClaim: daHours != null ? `${daHours.toFixed(1)}h invoiced` : "—",
        operationalReality: "No SOF timestamps available",
        variance: daHours != null ? `+${daHours.toFixed(1)}h (unverified)` : "—",
        isHighRisk,
      };
    }
    const diff = daHours != null && sofHours != null ? daHours - (sofHours + buffer) : null;
    return {
      vendorClaim: daHours != null ? `${daHours.toFixed(1)}h invoiced` : "—",
      operationalReality: sofHours != null ? `${sofHours.toFixed(1)}h (SOF actual)` : "—",
      variance:
        diff != null
          ? `+${diff.toFixed(1)}h overcharge`
          : "—",
      isHighRisk,
    };
  }

  // S-002: Berthage/Stay Verification
  if (discrepancy.rule_id === "S-002") {
    const daDays = raw.da_days as number | undefined;
    const actualDays = raw.actual_days as number | undefined;
    const source = raw.source as string | undefined;
    const diff = daDays != null && actualDays != null ? daDays - actualDays : null;
    return {
      vendorClaim: daDays != null ? `${daDays.toFixed(1)} days` : "—",
      operationalReality:
        actualDays != null
          ? `${actualDays.toFixed(1)} days (${source ?? "actual"})`
          : "—",
      variance:
        diff != null
          ? `${diff > 0 ? "+" : ""}${diff.toFixed(1)} days`
          : "—",
      isHighRisk,
    };
  }

  // S-003: Fuel Consumption Paradox
  if (discrepancy.rule_id === "S-003") {
    const fuelMt = raw.fuel_consumption_mt as number | undefined;
    const idleHours = raw.idle_hours as number | undefined;
    return {
      vendorClaim: fuelMt != null ? `${fuelMt.toFixed(2)} MT fuel` : "—",
      operationalReality:
        idleHours != null ? `${idleHours.toFixed(1)}h idle at anchorage` : "—",
      variance: "Operational alert",
      isHighRisk,
    };
  }

  // Fallback for unknown rules
  const vendorVal = raw.vendor_value ?? raw.da_hours ?? raw.da_days;
  const opVal = raw.operational_value ?? raw.sof_hours ?? raw.actual_days;
  return {
    vendorClaim: vendorVal != null ? String(vendorVal) : "—",
    operationalReality: opVal != null ? String(opVal) : "—",
    variance: raw.variance != null ? String(raw.variance) : "—",
    isHighRisk,
  };
}

export interface SideBySideAuditProps {
  discrepancies: DiscrepancyResponse[];
  portCallId: string;
  className?: string;
}

/**
 * Side-by-side audit table: Vendor Claims | Operational Reality | Variance.
 * Enables users to quickly identify and investigate discrepancies.
 */
export function SideBySideAudit({
  discrepancies,
  portCallId,
  className,
}: SideBySideAuditProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  if (discrepancies.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No discrepancies for this port call.
      </p>
    );
  }

  return (
    <div
      className={cn("overflow-x-auto", className)}
      role="region"
      aria-label="Side-by-side discrepancy audit"
    >
      <table
        className="w-full min-w-[600px] border-collapse text-left text-sm"
        role="table"
        aria-describedby="audit-table-desc"
      >
        <caption id="audit-table-desc" className="sr-only">
          Discrepancy audit: Vendor Claims vs Operational Reality vs Variance
        </caption>
        <thead>
          <tr className="border-b border-border bg-muted/50">
            <th
              scope="col"
              className="w-10 px-3 py-3 text-left font-medium text-muted-foreground"
              aria-label="Expand row"
            />
            <th
              scope="col"
              className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200"
            >
              Vendor Claims
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200"
            >
              Operational Reality
            </th>
            <th
              scope="col"
              className="px-4 py-3 font-semibold text-slate-700 dark:text-slate-200"
            >
              Variance
            </th>
          </tr>
        </thead>
        <tbody>
          {discrepancies.map((d) => {
            const rowData = extractRowData(d);
            const isExpanded = expandedIds.has(d.id);
            const ruleLabel = d.rule_id ? `Rule ${d.rule_id}` : "Unknown";

            return (
              <Fragment key={d.id}>
              <tr
                key={d.id}
                className="border-b border-border/80 transition-colors hover:bg-muted/30"
              >
                <td className="px-3 py-2 align-top">
                  <button
                    type="button"
                    onClick={() => toggleExpand(d.id)}
                    aria-expanded={isExpanded}
                    aria-label={isExpanded ? "Collapse details" : "Expand details"}
                    className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  >
                    {isExpanded ? (
                      <ChevronDown className="size-4" aria-hidden />
                    ) : (
                      <ChevronRight className="size-4" aria-hidden />
                    )}
                  </button>
                </td>
                <td className="px-4 py-3 align-top text-slate-800 dark:text-slate-200">
                  {rowData.vendorClaim}
                </td>
                <td className="px-4 py-3 align-top text-slate-800 dark:text-slate-200">
                  {rowData.operationalReality}
                </td>
                <td
                  className={cn(
                    "px-4 py-3 align-top font-medium",
                    rowData.isHighRisk &&
                      "text-red-600 dark:text-red-400"
                  )}
                >
                  {rowData.variance}
                </td>
              </tr>
              {isExpanded && (
                <tr
                  key={`${d.id}-expand`}
                  className="border-b border-border bg-muted/20"
                >
                  <td />
                  <td
                    colSpan={3}
                    className="px-4 py-3 text-muted-foreground"
                  >
                    <div className="space-y-2">
                      <p className="text-sm">{d.description}</p>
                      <div className="flex flex-wrap gap-2">
                        {d.rule_id && (
                          <span className="rounded bg-slate-200 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-600 dark:text-slate-200">
                            {ruleLabel}
                          </span>
                        )}
                        {d.estimated_loss && (
                          <span className="rounded bg-amber-200 px-2 py-0.5 text-xs font-medium text-amber-800 dark:bg-amber-900/50 dark:text-amber-300">
                            Est. loss: €{Number(d.estimated_loss).toLocaleString()}
                          </span>
                        )}
                        {(d.source_labels?.length ?? 0) > 0 ? (
                          <div className="flex flex-wrap gap-1.5">
                            {(d.source_labels ?? []).map((sl) => (
                              <span
                                key={sl.id}
                                className="inline-flex items-center rounded-md bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700 dark:bg-slate-700 dark:text-slate-200"
                                title={`Source: ${sl.label}`}
                              >
                                Source: {sl.label}
                              </span>
                            ))}
                          </div>
                        ) : d.source_documents.length > 0 ? (
                          <span className="text-xs text-muted-foreground">
                            {d.source_documents.length} source document(s) linked
                          </span>
                        ) : null}
                      </div>
                    </div>
                  </td>
                </tr>
              )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
