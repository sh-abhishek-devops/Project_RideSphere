import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "layouts/AppShell";
import { PublicLayout } from "layouts/PublicLayout";
import { CurrentRidePage } from "pages/CurrentRidePage";
import { DriverAvailabilityPage } from "pages/DriverAvailabilityPage";
import { DriverCurrentTripPage } from "pages/DriverCurrentTripPage";
import { DriverDashboardPage } from "pages/DriverDashboardPage";
import { DriverRegistrationPage } from "pages/DriverRegistrationPage";
import { DriverTripHistoryPage } from "pages/DriverTripHistoryPage";
import { LoginPage } from "pages/LoginPage";
import { NotFoundPage } from "pages/NotFoundPage";
import { OperationsDashboardPage } from "pages/OperationsDashboardPage";
import { RequestRidePage } from "pages/RequestRidePage";
import { RideHistoryPage } from "pages/RideHistoryPage";
import { RideInvestigationPage } from "pages/RideInvestigationPage";
import { RiderDashboardPage } from "pages/RiderDashboardPage";
import { RiderRegistrationPage } from "pages/RiderRegistrationPage";
import { SupportCaseDetailsPage } from "pages/SupportCaseDetailsPage";
import { SupportDashboardPage } from "pages/SupportDashboardPage";
import { UnauthorizedPage } from "pages/UnauthorizedPage";
import { ProtectedRoute } from "./ProtectedRoute";
import { PublicOnlyRoute } from "./PublicOnlyRoute";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicOnlyRoute />}>
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Navigate replace to="/login" />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register/rider" element={<RiderRegistrationPage />} />
          <Route path="/register/driver" element={<DriverRegistrationPage />} />
        </Route>
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppShell />}>
          <Route element={<ProtectedRoute allowedRoles={["RIDER"]} />}>
            <Route path="/rider/dashboard" element={<RiderDashboardPage />} />
            <Route path="/rider/request-ride" element={<RequestRidePage />} />
            <Route path="/rider/current-ride" element={<CurrentRidePage />} />
            <Route path="/rider/history" element={<RideHistoryPage />} />
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["DRIVER"]} />}>
            <Route path="/driver/dashboard" element={<DriverDashboardPage />} />
            <Route path="/driver/availability" element={<DriverAvailabilityPage />} />
            <Route path="/driver/current-trip" element={<DriverCurrentTripPage />} />
            <Route path="/driver/current-trip/:tripId" element={<DriverCurrentTripPage />} />
            <Route path="/driver/history" element={<DriverTripHistoryPage />} />
          </Route>

          <Route
            element={
              <ProtectedRoute allowedRoles={["SUPPORT_AGENT", "PAYMENT_AGENT", "OPERATIONS_MANAGER", "ADMIN"]} />
            }
          >
            <Route path="/support/dashboard" element={<SupportDashboardPage />} />
            <Route path="/support/cases" element={<SupportDashboardPage />} />
            <Route path="/support/cases/:caseId" element={<SupportCaseDetailsPage />} />
            <Route path="/support/investigations/:caseId" element={<RideInvestigationPage />} />
          </Route>

          <Route element={<ProtectedRoute allowedRoles={["OPERATIONS_MANAGER", "ADMIN"]} />}>
            <Route path="/operations/dashboard" element={<OperationsDashboardPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/unauthorized" element={<UnauthorizedPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
