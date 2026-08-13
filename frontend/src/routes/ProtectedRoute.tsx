import { Navigate, Outlet, useLocation } from "react-router-dom";

import { LoadingIndicator } from "components/LoadingIndicator";
import { useAuth } from "hooks/useAuth";
import type { UserRole } from "types/models";

interface ProtectedRouteProps {
  allowedRoles?: UserRole[];
}

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const auth = useAuth();
  const location = useLocation();

  if (auth.isInitializing) {
    return <LoadingIndicator label="Restoring your session..." />;
  }

  if (!auth.isAuthenticated) {
    return <Navigate replace state={{ from: location }} to="/login" />;
  }

  if (allowedRoles && auth.role && !allowedRoles.includes(auth.role)) {
    return <Navigate replace to="/unauthorized" />;
  }

  return <Outlet />;
}
