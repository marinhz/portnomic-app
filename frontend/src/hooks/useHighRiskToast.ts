import { useEffect, useRef } from "react";
import { useNavigate } from "react-router";
import { toast } from "sonner";
import type { DAAnomalyResponse } from "@/api/types";

const HIGH_RISK_SEVERITIES = ["high", "critical"] as const;
const SESSION_KEY = "shipflow-high-risk-toast-shown";

function getShownIds(): Set<string> {
  if (typeof sessionStorage === "undefined") return new Set();
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    if (!raw) return new Set();
    const arr = JSON.parse(raw) as string[];
    return new Set(Array.isArray(arr) ? arr : []);
  } catch {
    return new Set();
  }
}

function markShown(entityId: string): void {
  const set = getShownIds();
  set.add(entityId);
  try {
    sessionStorage.setItem(SESSION_KEY, JSON.stringify([...set]));
  } catch {
    // ignore
  }
}

function hasHighRiskAnomalies(anomalies: DAAnomalyResponse[]): boolean {
  return anomalies.some((a) =>
    HIGH_RISK_SEVERITIES.includes(a.severity as (typeof HIGH_RISK_SEVERITIES)[number]),
  );
}

function getHighRiskAnomalies(anomalies: DAAnomalyResponse[]) {
  return anomalies.filter((a) =>
    HIGH_RISK_SEVERITIES.includes(a.severity as (typeof HIGH_RISK_SEVERITIES)[number]),
  );
}

function formatRuleIds(anomalies: DAAnomalyResponse[]): string {
  const ids = [...new Set(anomalies.map((a) => a.rule_id))].sort();
  return ids.length <= 3 ? ids.join(", ") : `${ids.slice(0, 2).join(", ")} +${ids.length - 2}`;
}

export type HighRiskToastTarget = "da" | "email";

export interface UseHighRiskToastOptions {
  anomalies: DAAnomalyResponse[];
  entityId: string | undefined;
  target: HighRiskToastTarget;
}

/**
 * Shows a Sonner toast when high/critical anomalies are detected.
 * Deduplicates by entity ID per session (no duplicate toasts for same invoice).
 */
export function useHighRiskToast({
  anomalies,
  entityId,
  target,
}: UseHighRiskToastOptions): void {
  const navigate = useNavigate();
  const hasTriggeredRef = useRef(false);

  useEffect(() => {
    if (!entityId || anomalies.length === 0) return;
    if (!hasHighRiskAnomalies(anomalies)) return;

    const shown = getShownIds();
    if (shown.has(entityId)) return;

    const highRisk = getHighRiskAnomalies(anomalies);
    const count = highRisk.length;
    const ruleIds = formatRuleIds(highRisk);
    const description = `${count} anomaly(ies) found (${ruleIds})`;

    const linkPath = target === "da" ? `/da/${entityId}` : `/emails/${entityId}`;
    const linkLabel = target === "da" ? "View DA" : "View email";

    hasTriggeredRef.current = true;
    markShown(entityId);

    toast.error("High Risk Invoice Detected", {
      description,
      action: {
        label: linkLabel,
        onClick: () => {
          navigate(linkPath);
        },
      },
      duration: 8000,
    });
  }, [anomalies, entityId, target, navigate]);
}
