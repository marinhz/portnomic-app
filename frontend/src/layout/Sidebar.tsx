import { NavLink } from "react-router";
import {
  LayoutDashboard,
  Ship,
  Anchor,
  Mail,
  FileText,
  Settings,
  X,
  CreditCard,
  Leaf,
  Sparkles,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useAuth } from "@/auth/AuthContext";

type SidebarProps = {
  onClose: () => void;
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
};

function NavItem({
  to,
  end,
  icon: Icon,
  label,
  isCollapsed,
}: {
  to: string;
  end?: boolean;
  icon: React.ComponentType<{ className?: string; style?: React.CSSProperties }>;
  label: string;
  isCollapsed: boolean;
}) {
  const link = (
    <NavLink
      to={to}
      end={end}
        className={({ isActive }) =>
        `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mint-500 focus-visible:ring-offset-2 dark:focus-visible:ring-offset-navy-950 ${
          isCollapsed ? "gap-0 justify-center" : ""
        } ${
          isActive
            ? "bg-mint-100 text-navy-800 dark:bg-navy-800 dark:text-mint-200"
            : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100"
        }`
      }
      aria-label={isCollapsed ? label : undefined}
    >
      <Icon className="size-5 shrink-0" />
      {!isCollapsed && <span>{label}</span>}
    </NavLink>
  );

  if (isCollapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="inline-flex w-full">{link}</span>
        </TooltipTrigger>
        <TooltipContent side="right" sideOffset={8}>
          <span>{label}</span>
        </TooltipContent>
      </Tooltip>
    );
  }
  return link;
}

function SectionDivider({
  label,
  isCollapsed,
}: {
  label: string;
  isCollapsed: boolean;
}) {
  return (
    <div className="px-2 pt-3 pb-1.5">
      {isCollapsed ? (
        <div className="h-px" aria-hidden />
      ) : (
        <p className="px-1 text-[11px] font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
          {label}
        </p>
      )}
    </div>
  );
}

export function Sidebar({
  onClose,
  isCollapsed = false,
  onToggleCollapse,
}: SidebarProps) {
  const { user } = useAuth();

  const hasDARead = user?.permissions.includes("da:read") ?? false;
  const hasBillingManage =
    user?.permissions.includes("billing:manage") ?? false;
  const hasSettingsWrite =
    user?.permissions.includes("settings:write") ?? false;
  const isPlatformAdmin = user?.is_platform_admin ?? false;
  const showOtherSettings =
    hasBillingManage || hasSettingsWrite || isPlatformAdmin;

  return (
    <div className="flex h-full flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div
        className={`flex h-14 shrink-0 items-center gap-3 border-b border-slate-200 px-4 dark:border-slate-700`}
      >
        <img
          src="/Portnomic.svg"
          alt="Portnomic"
          className="h-8 w-8 shrink-0 rounded object-contain"
        />
        {!isCollapsed && (
          <span className="truncate text-base font-semibold tracking-tight text-slate-900 dark:text-slate-100">
            Portnomic
          </span>
        )}
        <button
          onClick={onClose}
          className="ml-auto shrink-0 rounded-md p-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200 lg:hidden"
          aria-label="Close sidebar"
        >
          <X className="size-5" />
        </button>
      </div>

      {/* Navigation */}
      <nav
        className={`min-h-0 flex-1 space-y-0.5 overflow-y-auto overflow-x-hidden px-3 py-4`}
        onClick={onClose}
      >
        <SectionDivider label="Operations" isCollapsed={isCollapsed} />
        <NavItem
          to="/"
          end
          icon={LayoutDashboard}
          label="Dashboard"
          isCollapsed={isCollapsed}
        />
        <NavItem
          to="/vessels"
          icon={Ship}
          label="Vessels"
          isCollapsed={isCollapsed}
        />
        <NavItem
          to="/port-calls"
          icon={Anchor}
          label="Port Calls"
          isCollapsed={isCollapsed}
        />
        {hasDARead && (
          <NavItem
            to="/da"
            icon={FileText}
            label="Disbursement Accounts"
            isCollapsed={isCollapsed}
          />
        )}

        <SectionDivider label="Inbox & Reports" isCollapsed={isCollapsed} />
        <NavItem
          to="/emails"
          icon={Mail}
          label="Emails"
          isCollapsed={isCollapsed}
        />
        <NavItem
          to="/emissions"
          icon={Leaf}
          label="Emissions"
          isCollapsed={isCollapsed}
        />

        {showOtherSettings && (
          <>
            <SectionDivider label="Settings" isCollapsed={isCollapsed} />
            <NavItem
              to="/settings/integrations"
              icon={Settings}
              label="Integrations"
              isCollapsed={isCollapsed}
            />
            {(hasSettingsWrite || isPlatformAdmin) && (
              <NavItem
                to="/settings/ai"
                icon={Sparkles}
                label="AI Settings"
                isCollapsed={isCollapsed}
              />
            )}
            {(hasBillingManage || isPlatformAdmin) && (
              <NavItem
                to="/settings/billing"
                icon={CreditCard}
                label="Billing"
                isCollapsed={isCollapsed}
              />
            )}
          </>
        )}

      </nav>

      {/* Collapse toggle */}
      {onToggleCollapse && (
        <div className="shrink-0 border-t border-slate-200 px-3 py-2 dark:border-slate-700">
          {isCollapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onToggleCollapse}
                  className="flex w-full items-center justify-center rounded-lg px-3 py-2 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
                  aria-label="Expand sidebar"
                  type="button"
                >
                  <ChevronsRight className="size-5 shrink-0" />
                </button>
              </TooltipTrigger>
              <TooltipContent side="right" sideOffset={8}>Expand sidebar</TooltipContent>
            </Tooltip>
          ) : (
            <button
              onClick={onToggleCollapse}
              className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
              aria-label="Collapse sidebar"
              type="button"
            >
              <ChevronsLeft className="size-5 shrink-0" />
              <span>Collapse</span>
            </button>
          )}
        </div>
      )}

    </div>
  );
}
