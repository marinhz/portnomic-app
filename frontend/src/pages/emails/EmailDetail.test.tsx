import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { createMemoryRouter, RouterProvider } from "react-router";
import { EmailDetail } from "./EmailDetail";
import { EMISSION_REPORT_CREATED } from "@/events/emissions";

const mockEmail = {
  id: "email-123",
  external_id: "ext-1",
  subject: "Test Email",
  sender: "sender@test.com",
  body_text: "Body",
  body_html: null,
  processing_status: "pending" as const,
  ai_raw_output: null,
  prompt_version: null,
  error_reason: null,
  retry_count: 0,
  received_at: "2025-01-01T00:00:00Z",
  created_at: "2025-01-01T00:00:00Z",
};

const mockParseJob = {
  id: "job-456",
  email_id: "email-123",
  status: "completed",
  result: null,
  error_message: null,
  prompt_version: null,
  started_at: "2025-01-01T00:00:00Z",
  completed_at: "2025-01-01T00:00:01Z",
  created_at: "2025-01-01T00:00:00Z",
};

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => ({
    user: { id: "u1", permissions: [] },
    isAuthenticated: true,
    isLoading: false,
  }),
}));

const api = (await import("@/api/client")).default;

function createRouter(initialEntries = ["/emails/email-123"]) {
  const router = createMemoryRouter(
    [
      {
        path: "/emails/:emailId",
        element: <EmailDetail />,
      },
      {
        path: "/emails",
        element: <div>Email list</div>,
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

describe("EmailDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emails/")) {
        return Promise.resolve({
          data: { data: mockEmail },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });
  });

  it("renders email detail and stays on page after parse success (no 404 redirect)", async () => {
    let emailCallCount = 0;
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emails/email-123") && !url.includes("/ai/parse/")) {
        emailCallCount++;
        return Promise.resolve({
          data: {
            data: {
              ...mockEmail,
              processing_status:
                emailCallCount === 1 ? "pending" : "completed",
              ai_raw_output:
                emailCallCount > 1
                  ? { vessel_name: "Test Vessel", line_items: [], summary: "Parsed" }
                  : null,
            },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/ai/parse/")) {
        return Promise.resolve({
          data: {
            data: {
              ...mockParseJob,
              status: "completed",
              result: { vessel_name: "Test Vessel", line_items: [] },
            },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });

    const router = createRouter();
    render(<RouterProvider router={router} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /parse with ai/i })).toBeInTheDocument();
    });

    vi.mocked(api.post).mockResolvedValue({
      data: { data: { ...mockParseJob, id: "job-456" } },
      status: 202,
      config: {} as never,
      headers: {},
      statusText: "",
    });

    await userEvent.click(screen.getByRole("button", { name: /parse with ai/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith("/emails/email-123");
    });

    expect(router.state.location.pathname).toBe("/emails/email-123");
  });

  it("shows View emission report link with correct path when parse has emission_report_id", async () => {
    let emailCallCount = 0;
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emails/email-123") && !url.includes("/ai/parse/")) {
        emailCallCount++;
        return Promise.resolve({
          data: {
            data: {
              ...mockEmail,
              processing_status: emailCallCount === 1 ? "pending" : "completed",
              ai_raw_output:
                emailCallCount > 1
                  ? { vessel_name: "Vessel", fuel_entries: [] }
                  : null,
            },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/ai/parse/")) {
        return Promise.resolve({
          data: {
            data: {
              ...mockParseJob,
              status: "completed",
              result: {
                type: "emission",
                emission_report_id: "report-uuid-789",
              },
            },
          },
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
      expect(screen.getByRole("button", { name: /parse with ai/i })).toBeInTheDocument();
    });

    vi.mocked(api.post).mockResolvedValue({
      data: { data: { ...mockParseJob, id: "job-456" } },
      status: 202,
      config: {} as never,
      headers: {},
      statusText: "",
    });

    await userEvent.click(screen.getByRole("button", { name: /parse with ai/i }));

    await waitFor(() => {
      const link = screen.getByRole("link", { name: /view emission report/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute("href", "/emissions/reports/report-uuid-789");
    });
  });

  it("dispatches emission-report-created when parse completes with emission_report_id", async () => {
    const capturedEvents: CustomEvent[] = [];
    const handler = (e: Event) => capturedEvents.push(e as CustomEvent);
    window.addEventListener(EMISSION_REPORT_CREATED, handler);

    let emailCallCount = 0;
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emails/email-123") && !url.includes("/ai/parse/")) {
        emailCallCount++;
        return Promise.resolve({
          data: {
            data: {
              ...mockEmail,
              processing_status: emailCallCount === 1 ? "pending" : "completed",
              ai_raw_output:
                emailCallCount > 1 ? { vessel_name: "Vessel" } : null,
            },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/ai/parse/")) {
        return Promise.resolve({
          data: {
            data: {
              ...mockParseJob,
              status: "completed",
              result: {
                type: "emission",
                emission_report_id: "report-uuid-789",
              },
            },
          },
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
      expect(screen.getByRole("button", { name: /parse with ai/i })).toBeInTheDocument();
    });

    vi.mocked(api.post).mockResolvedValue({
      data: { data: { ...mockParseJob, id: "job-456" } },
      status: 202,
      config: {} as never,
      headers: {},
      statusText: "",
    });

    await userEvent.click(screen.getByRole("button", { name: /parse with ai/i }));

    await waitFor(
      () => {
        expect(capturedEvents).toHaveLength(1);
        expect(capturedEvents[0].detail).toEqual({ reportId: "report-uuid-789" });
      },
      { timeout: 3000 },
    );

    window.removeEventListener(EMISSION_REPORT_CREATED, handler);
  });

  it("renders parsed result without crashing when line_items is missing (emission)", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: {
        data: {
          ...mockEmail,
          processing_status: "completed",
          ai_raw_output: {
            vessel_name: "Emission Vessel",
            imo_number: "1234567",
            fuel_entries: [{ fuel_type: "VLSFO", consumption_mt: 10, operational_status: "at_sea_cruising" }],
          },
        },
      },
      status: 200,
      config: {} as never,
      headers: {},
      statusText: "",
    });

    render(<RouterProvider router={createRouter()} />);

    await waitFor(() => {
      expect(screen.getByText("Parsed Result")).toBeInTheDocument();
    });

    expect(screen.getByText("Emission Vessel")).toBeInTheDocument();
  });

  it("shows error state when parse fails, not 404", async () => {
    let emailCallCount = 0;
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/emails/email-123") && !url.includes("/ai/parse/")) {
        emailCallCount++;
        return Promise.resolve({
          data: {
            data: {
              ...mockEmail,
              processing_status: emailCallCount === 1 ? "pending" : "failed",
              error_reason: emailCallCount > 1 ? "Parse failed" : null,
            },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/ai/parse/")) {
        return Promise.resolve({
          data: {
            data: {
              ...mockParseJob,
              status: "failed",
              error_message: "Parse failed",
            },
          },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });

    vi.mocked(api.post).mockResolvedValue({
      data: { data: { ...mockParseJob, id: "job-456" } },
      status: 202,
      config: {} as never,
      headers: {},
      statusText: "",
    });

    render(<RouterProvider router={createRouter()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /parse with ai/i })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: /parse with ai/i }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /retry parse/i })).toBeInTheDocument();
    });

    expect(screen.queryByText("Page not found")).not.toBeInTheDocument();
  });
});
