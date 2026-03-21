import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter } from "react-router";
import { SentinelAlert } from "./SentinelAlert";
import type { DiscrepancyResponse } from "@/api/types";

const mockDiscrepancies: DiscrepancyResponse[] = [
  {
    id: "1",
    tenant_id: "t1",
    port_call_id: "pc1",
    severity: "high",
    description: "Time overlap detected",
    estimated_loss: "100.00",
    source_documents: [],
    rule_id: "S-001",
    raw_evidence: null,
    created_at: "2025-03-21T12:00:00Z",
  },
  {
    id: "2",
    tenant_id: "t1",
    port_call_id: "pc1",
    severity: "medium",
    description: "Potential variance",
    estimated_loss: null,
    source_documents: [],
    rule_id: null,
    raw_evidence: null,
    created_at: "2025-03-21T12:00:00Z",
  },
];

function renderWithRouter(ui: React.ReactElement) {
  const router = createMemoryRouter(
    [{ path: "/", element: ui }],
    { initialEntries: ["/"] }
  );
  return render(<RouterProvider router={router} />);
}

describe("SentinelAlert", () => {
  it("returns null when discrepancies are empty", () => {
    const { container } = renderWithRouter(
      <SentinelAlert discrepancies={[]} portCallId="pc1" />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders when discrepancies exist", () => {
    renderWithRouter(
      <SentinelAlert discrepancies={mockDiscrepancies} portCallId="pc1" />
    );
    expect(
      screen.getByRole("alert", { name: /sentinel operational gap alerts/i })
    ).toBeInTheDocument();
    expect(screen.getByText(/sentinel alerts/i)).toBeInTheDocument();
    expect(screen.getByText(/1 high-risk, 1 potential errors/i)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /view audit details/i })).toBeInTheDocument();
  });

  it("calls onDismiss when Dismiss is clicked", async () => {
    const onDismiss = vi.fn();
    renderWithRouter(
      <SentinelAlert
        discrepancies={mockDiscrepancies}
        portCallId="pc1"
        onDismiss={onDismiss}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /dismiss/i }));
    expect(onDismiss).toHaveBeenCalledTimes(1);
  });
});
