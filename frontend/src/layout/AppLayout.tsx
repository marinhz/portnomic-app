import { useState, useEffect, useLayoutEffect } from "react";
import { Outlet, Link, useNavigate, useLocation } from "react-router";
import { Menu, Sun, Moon, ChevronDown, User, Users, Shield, Building2, LogOut } from "lucide-react";
import { useAuth } from "@/auth/AuthContext";
import { useTheme } from "@/hooks/useTheme";
import { Sidebar } from "./Sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

function getInitialCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, toggle: toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(getInitialCollapsed);

  /** Close mobile drawer + scrim on navigation so the backdrop cannot block the next screen (e.g. after login redirect). */
  useLayoutEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  const hasAdminUsers = user?.permissions.includes("admin:users") ?? false;
  const hasAdminRoles = user?.permissions.includes("admin:roles") ?? false;
  const isPlatformAdmin = user?.is_platform_admin ?? false;
  const showAdmin = hasAdminUsers || hasAdminRoles || isPlatformAdmin;

  useEffect(() => {
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 overflow-x-hidden transform border-r border-slate-200 bg-white shadow-sm transition-[width,transform] duration-200 dark:border-slate-700 dark:bg-slate-900 lg:relative lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        } ${sidebarOpen ? "w-60" : sidebarCollapsed ? "w-16" : "w-60"}`}
      >
        <Sidebar
          onClose={() => setSidebarOpen(false)}
          isCollapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
        />
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-700 dark:bg-slate-900">
          <button
            onClick={() => setSidebarOpen(true)}
            className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 lg:hidden"
            aria-label="Open sidebar"
          >
            <Menu className="size-5" />
          </button>

          <div className="hidden lg:block" />

          <div className="flex items-center gap-4">
            <button
              onClick={toggleTheme}
              className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? (
                <Sun className="size-5" />
              ) : (
                <Moon className="size-5" />
              )}
            </button>

            <DropdownMenu modal={false}>
              <DropdownMenuTrigger asChild>
                <button
                  type="button"
                  className="flex items-center gap-3 rounded-lg px-2 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mint-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-navy-950"
                  aria-label="User menu"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-full bg-mint-100 text-xs font-semibold text-navy-800 dark:bg-navy-800 dark:text-mint-200">
                    {user?.email?.charAt(0).toUpperCase()}
                  </div>
                  <span className="hidden sm:inline">{user?.email}</span>
                  <ChevronDown className="size-4 shrink-0" />
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link to="/settings/profile" className="flex items-center gap-2">
                    <User className="size-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                {showAdmin && (
                  <>
                    <DropdownMenuSeparator />
                    <DropdownMenuLabel>Admin</DropdownMenuLabel>
                    {hasAdminUsers && (
                      <DropdownMenuItem asChild>
                        <Link to="/admin/users" className="flex items-center gap-2">
                          <Users className="size-4" />
                          Users
                        </Link>
                      </DropdownMenuItem>
                    )}
                    {hasAdminRoles && (
                      <DropdownMenuItem asChild>
                        <Link to="/admin/roles" className="flex items-center gap-2">
                          <Shield className="size-4" />
                          Roles
                        </Link>
                      </DropdownMenuItem>
                    )}
                    {isPlatformAdmin && (
                      <DropdownMenuItem asChild>
                        <Link to="/admin/companies" className="flex items-center gap-2">
                          <Building2 className="size-4" />
                          Companies
                        </Link>
                      </DropdownMenuItem>
                    )}
                  </>
                )}
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="flex items-center gap-2">
                  <LogOut className="size-4" />
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-slate-50 p-6 dark:bg-slate-950 dark:text-slate-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
