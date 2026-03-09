import { Navigate, Outlet } from "react-router";
import { useAuth } from "./AuthContext";

/**
 * Protects AI Settings routes. Only users with settings:write can access.
 * Redirects to Integrations settings if unauthorized.
 */
export function AdminAISettingsRoute() {
  const { user } = useAuth();
  const hasSettingsWrite = user?.permissions.includes("settings:write") ?? false;
  const isPlatformAdmin = user?.is_platform_admin ?? false;

  if (!hasSettingsWrite && !isPlatformAdmin) {
    return (
      <Navigate
        to="/settings/integrations"
        replace
        state={{ message: "AI settings require admin permissions." }}
      />
    );
  }

  return <Outlet />;
}
