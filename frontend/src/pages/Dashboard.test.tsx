import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router";
import { Dashboard } from "./Dashboard";

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => ({
    user: { email: "test@example.com", permissions: ["da:read"], is_platform_admin: false },
  }),
}));

vi.mock("@/api/client", () => ({
  default: {
    get: vi.fn(),
  },
}));

const api = (await import("@/api/client")).default;

function createRouter() {
  return createMemoryRouter(
    [{ path: "/", element: <Dashboard /> }],
    { initialEntries: ["/"] },
  );
}

describe("Dashboard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/vessels")) {
        return Promise.resolve({
          data: { data: [], meta: { total: 0 } },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/port-calls")) {
        return Promise.resolve({
          data: { data: [], meta: { total: 0 } },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      if (url.includes("/da")) {
        return Promise.resolve({
          data: { data: [], meta: { total: 0 } },
          status: 200,
          config: {} as never,
          headers: {},
          statusText: "",
        });
      }
      return Promise.reject(new Error("Unexpected GET"));
    });
  });

  it("Task 7.4: Summary cards use size-6 icons", async () => {
    render(<RouterProvider router={createRouter()} />);

    await waitFor(() => {
      expect(screen.getByText("Welcome back, test")).toBeInTheDocument();
    });

    // Task 7.4: Summary card icons should have size-6 class
    const size6Icons = document.querySelectorAll(".size-6");
    expect(size6Icons.length).toBeGreaterThanOrEqual(4); // LayoutDashboard + Ship, Anchor, Activity, FileText
  });
});
