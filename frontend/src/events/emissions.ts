/**
 * Custom event dispatched when a new emission report is created (e.g. after AI parse).
 * Listeners (e.g. EmissionsDashboard) can refetch data to avoid stale values.
 */
export const EMISSION_REPORT_CREATED = "emission-report-created";

export function dispatchEmissionReportCreated(reportId: string): void {
  window.dispatchEvent(
    new CustomEvent(EMISSION_REPORT_CREATED, { detail: { reportId } }),
  );
}
