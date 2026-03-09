import { Navigate, Outlet } from "react-router";
import { useAuth } from "./AuthContext";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export function PlatformAdminRoute() {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!user?.is_platform_admin) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
