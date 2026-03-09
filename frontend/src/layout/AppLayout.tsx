import { useState, useEffect } from "react";
import { Outlet, useNavigate } from "react-router";
import { Menu, Sun, Moon } from "lucide-react";
import { useAuth } from "@/auth/AuthContext";
import { useTheme } from "@/hooks/useTheme";
import { Sidebar } from "./Sidebar";

const SIDEBAR_COLLAPSED_KEY = "sidebar-collapsed";

function getInitialCollapsed(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === "true";
}

export function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { theme, toggle: toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(getInitialCollapsed);

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

            <div className="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-mint-100 text-xs font-semibold text-navy-800 dark:bg-navy-800 dark:text-mint-200">
                {user?.email?.charAt(0).toUpperCase()}
              </div>
              <span className="hidden sm:inline">{user?.email}</span>
            </div>

            <button
              onClick={handleLogout}
              className="rounded-lg px-3 py-1.5 text-sm text-slate-600 transition-colors hover:bg-slate-100 hover:text-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
            >
              Logout
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto bg-slate-50 p-6 dark:bg-slate-950 dark:text-slate-100">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
