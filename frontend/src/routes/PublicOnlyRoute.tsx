import { Navigate, Outlet } from "react-router-dom";

import { LoadingIndicator } from "components/LoadingIndicator";
import { useAuth } from "hooks/useAuth";
import { getDefaultRouteForRole } from "utils/app";

export function PublicOnlyRoute() {
  const auth = useAuth();

  if (auth.isInitializing) {
    return <LoadingIndicator label="Loading your session..." />;
  }

  if (auth.isAuthenticated && auth.role) {
    return <Navigate replace to={getDefaultRouteForRole(auth.role)} />;
  }

  return <Outlet />;
}
