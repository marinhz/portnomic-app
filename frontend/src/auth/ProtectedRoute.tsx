import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "./AuthContext";
import { LoadingSpinner } from "@/components/LoadingSpinner";

export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
}
