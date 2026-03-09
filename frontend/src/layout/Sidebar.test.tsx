import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Sidebar } from "./Sidebar";

const mockUser = {
  id: "1",
  tenant_id: "t1",
  email: "user@portnomic.com",
  role_id: "r1",
  permissions: ["da:read", "admin:users"],
  mfa_enabled: false,
};

vi.mock("@/auth/AuthContext", () => ({
  useAuth: () => ({
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: vi.fn(),
    logout: vi.fn(),
    completeMfa: vi.fn(),
  }),
}));

function renderSidebar(props: {
  onClose?: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
} = {}) {
  const defaultProps = {
    onClose: vi.fn(),
    isCollapsed: false,
    onToggleCollapse: undefined as (() => void) | undefined,
    ...props,
  };
  return render(
    <MemoryRouter>
      <TooltipProvider>
        <Sidebar
          onClose={defaultProps.onClose}
          isCollapsed={defaultProps.isCollapsed}
          onToggleCollapse={defaultProps.onToggleCollapse}
        />
      </TooltipProvider>
    </MemoryRouter>,
  );
}

describe("Sidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders Portnomic branding", () => {
    renderSidebar();
    expect(screen.getByText("Portnomic")).toBeInTheDocument();
  });

  it("renders main nav links", () => {
    renderSidebar();
    expect(screen.getByRole("link", { name: /dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /vessels/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /port calls/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /emails/i })).toBeInTheDocument();
  });

  it("renders IA structure: Operations, Inbox & Reports, Settings, Admin sections", () => {
    renderSidebar();
    expect(screen.getByText("Operations")).toBeInTheDocument();
    expect(screen.getByText("Inbox & Reports")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
    expect(screen.getByText("Admin")).toBeInTheDocument();
  });

  it("places Disbursement Accounts in Operations (after Port Calls)", () => {
    renderSidebar();
    const links = screen.getAllByRole("link");
    const labels = links.map((l) => l.textContent?.trim() ?? l.getAttribute("aria-label") ?? "");
    const portCallsIdx = labels.findIndex((l) => /port calls/i.test(l));
    const daIdx = labels.findIndex((l) => /disbursement accounts/i.test(l));
    expect(portCallsIdx).toBeGreaterThan(-1);
    expect(daIdx).toBeGreaterThan(-1);
    expect(daIdx).toBe(portCallsIdx + 1);
  });

  it("renders DA link when user has da:read permission", () => {
    renderSidebar();
    expect(screen.getByRole("link", { name: /disbursement accounts/i })).toBeInTheDocument();
  });

  it("renders admin links when user has admin permissions", () => {
    renderSidebar();
    expect(screen.getByRole("link", { name: /users/i })).toBeInTheDocument();
  });

  it("renders user email in footer", () => {
    renderSidebar();
    expect(screen.getByText("user@portnomic.com")).toBeInTheDocument();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    renderSidebar({ onClose });
    const closeBtn = screen.getByRole("button", { name: /close sidebar/i });
    fireEvent.click(closeBtn);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("calls onToggleCollapse when toggle is clicked", () => {
    const onToggleCollapse = vi.fn();
    renderSidebar({ onToggleCollapse });
    const toggleBtn = screen.getByRole("button", { name: /collapse sidebar/i });
    fireEvent.click(toggleBtn);
    expect(onToggleCollapse).toHaveBeenCalledTimes(1);
  });

  describe("collapsed state", () => {
    it("hides link text when collapsed", () => {
      renderSidebar({ isCollapsed: true });
      expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
      expect(screen.queryByText("Portnomic")).not.toBeInTheDocument();
    });

    it("shows icons with tooltips when collapsed", () => {
      renderSidebar({ isCollapsed: true });
      const dashboardLink = screen.getByRole("link", { name: /dashboard/i });
      expect(dashboardLink).toBeInTheDocument();
      // Tooltip content is rendered in a portal and shown on hover; link is the trigger
    });

    it("shows expand button when collapsed and onToggleCollapse provided", () => {
      renderSidebar({ isCollapsed: true, onToggleCollapse: vi.fn() });
      expect(screen.getByRole("button", { name: /expand sidebar/i })).toBeInTheDocument();
    });
  });
});
