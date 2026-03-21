import { describe, it, expect } from "vitest";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SideBySideAudit } from "./SideBySideAudit";
import type { DiscrepancyResponse } from "@/api/types";

const mockDiscrepancyS001: DiscrepancyResponse = {
  id: "1",
  tenant_id: "t1",
  port_call_id: "pc1",
  severity: "high",
  description: "Overcharged tug hours: DA invoiced 8.0h, SOF actual 5.5h.",
  estimated_loss: "250.00",
  source_documents: ["doc1", "doc2"],
  rule_id: "S-001",
  raw_evidence: {
    da_hours: 8,
    sof_hours: 5.5,
    buffer_hours: 0.5,
  },
  created_at: "2025-03-21T12:00:00Z",
};

const mockDiscrepancyS002: DiscrepancyResponse = {
  id: "2",
  tenant_id: "t1",
  port_call_id: "pc1",
  severity: "medium",
  description: "Berthage mismatch: DA claims 3.0 days, actual 2.2 days.",
  estimated_loss: null,
  source_documents: [],
  rule_id: "S-002",
  raw_evidence: {
    da_days: 3,
    actual_days: 2.2,
    source: "ais",
  },
  created_at: "2025-03-21T12:00:00Z",
};

describe("SideBySideAudit", () => {
  it("renders empty state when no discrepancies", () => {
    render(<SideBySideAudit discrepancies={[]} portCallId="pc1" />);
    expect(screen.getByText(/no discrepancies for this port call/i)).toBeInTheDocument();
  });

  it("renders three-column layout with headers", () => {
    render(
      <SideBySideAudit
        discrepancies={[mockDiscrepancyS001]}
        portCallId="pc1"
      />
    );
    expect(screen.getByRole("table")).toBeInTheDocument();
    expect(screen.getByText("Vendor Claims")).toBeInTheDocument();
    expect(screen.getByText("Operational Reality")).toBeInTheDocument();
    expect(screen.getByText("Variance")).toBeInTheDocument();
  });

  it("displays vendor claims, operational reality, and variance per discrepancy", () => {
    render(
      <SideBySideAudit
        discrepancies={[mockDiscrepancyS001, mockDiscrepancyS002]}
        portCallId="pc1"
      />
    );
    const rows = screen.getAllByRole("row");
    expect(rows.length).toBeGreaterThanOrEqual(3); // header + 2 data + possible expand rows
    expect(screen.getByText(/8\.0h invoiced/)).toBeInTheDocument();
    expect(screen.getByText(/5\.5h \(SOF actual\)/)).toBeInTheDocument();
    expect(screen.getByText(/3\.0 days/)).toBeInTheDocument();
    expect(screen.getByText(/2\.2 days \(ais\)/)).toBeInTheDocument();
  });

  it("expands row to show description and source documents", async () => {
    render(
      <SideBySideAudit
        discrepancies={[mockDiscrepancyS001]}
        portCallId="pc1"
      />
    );
    const expandButton = screen.getByRole("button", {
      name: /expand details/i,
    });
    await userEvent.click(expandButton);
    expect(screen.getByText(/overcharged tug hours/i)).toBeInTheDocument();
    expect(screen.getByText(/est\. loss: €250/i)).toBeInTheDocument();
  });
});
