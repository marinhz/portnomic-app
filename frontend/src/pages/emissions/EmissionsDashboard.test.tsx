import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { EmissionsDashboard } from "./EmissionsDashboard";
import { EMISSION_REPORT_CREATED } from "@/events/emissions";

const mockSummary = {
  total_co2_mt: 10.5,
  total_eua_estimate_eur: 500,
  voyage_count: 2,
  compliance: { green: 1, yellow: 1, red: 0 },
};

const mockReports = [
  {
    id: "report-1",
    vessel_id: "v1",
    vessel_name: "Test Vessel",
    voyage_id: null,
    report_date: "2025-01-01",
    co2_mt: 5.25,
    eua_estimate_eur: 250,
    compliance_status: "green" as const,
    verification_status: "verified" as const,
    source_email_id: "email-1",
    created_at: "2025-01-01T00:00:00Z",
  },
];

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

const api = (await import("@/api/client")).default;

function createRouter(initialEntries = ["/emissions"]) {
  const router = createMemoryRouter(
    [
      {
        path: "/emissions",
        element: <EmissionsDashboard />,
      },
      {
        path: "/emissions/reports/:id",
        element: <div>Emission report</div>,
      },
    ],
    { initialEntries },
  );
  return router;
}

describe("EmissionsDashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emissions/summary")) {
        return Promise.resolve({
          data: mockSummary,
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/emissions/reports") && !url.includes("/export")) {
        return Promise.resolve({
          data: {
            data: mockReports,
            meta: { total: 1, page: 1, per_page: 20 },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });
  });

  it("fetches summary and reports on mount", async () => {
    render(<RouterProvider router={createRouter()} />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith(
        "/emissions/summary",
        expect.objectContaining({ params: {} }),
      );
      expect(api.get).toHaveBeenCalledWith(
        "/emissions/reports",
        expect.objectContaining({
          params: expect.objectContaining({ page: 1, per_page: 20 }),
        }),
      );
    });

    await waitFor(() => {
      expect(screen.getByText("Emissions Dashboard")).toBeInTheDocument();
      expect(screen.getByText("10.50")).toBeInTheDocument();
      expect(screen.getByText("Test Vessel")).toBeInTheDocument();
    });
  });

  it("refetches when emission-report-created event is dispatched", async () => {
    render(<RouterProvider router={createRouter()} />);

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(2);
    });

    const updatedReports = [
      ...mockReports,
      {
        id: "report-2",
        vessel_id: "v2",
        vessel_name: "New Vessel",
        voyage_id: null,
        report_date: "2025-01-02",
        co2_mt: 5.25,
        eua_estimate_eur: 250,
        compliance_status: "green" as const,
        verification_status: "pending" as const,
        source_email_id: "email-2",
        created_at: "2025-01-02T00:00:00Z",
      },
    ];

    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emissions/summary")) {
        return Promise.resolve({
          data: { ...mockSummary, voyage_count: 3 },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/emissions/reports") && !url.includes("/export")) {
        return Promise.resolve({
          data: {
            data: updatedReports,
            meta: { total: 2, page: 1, per_page: 20 },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });

    window.dispatchEvent(
      new CustomEvent(EMISSION_REPORT_CREATED, { detail: { reportId: "report-2" } }),
    );

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledTimes(4);
    });

    await waitFor(() => {
      expect(screen.getByText("New Vessel")).toBeInTheDocument();
    });
  });

  it("shows empty state when no reports", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emissions/summary")) {
        return Promise.resolve({
          data: { ...mockSummary, voyage_count: 0 },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/emissions/reports") && !url.includes("/export")) {
        return Promise.resolve({
          data: { data: [], meta: { total: 0, page: 1, per_page: 20 } },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });

    render(<RouterProvider router={createRouter()} />);

    await waitFor(() => {
      expect(screen.getByText("No emission reports yet")).toBeInTheDocument();
    });
  });
});
