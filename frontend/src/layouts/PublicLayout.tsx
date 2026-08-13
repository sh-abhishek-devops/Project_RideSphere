import { Link, Outlet } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { LoadingIndicator } from "components/LoadingIndicator";
import { fetchHealthStatus } from "services/healthService";

export function PublicLayout() {
  const healthQuery = useQuery({
    queryKey: ["health-status"],
    queryFn: fetchHealthStatus,
    retry: 1
  });

  return (
    <div className="public-shell">
      <section className="public-shell__hero">
        <div className="public-shell__panel">
          <p className="eyebrow">Ride operations platform</p>
          <h1>Coordinate riders, drivers, and support with one shared system.</h1>
          <p className="subtitle">
            RideSphere is a fictional platform for trip dispatch, operational visibility, and service support.
          </p>
          <div className="public-shell__links">
            <Link className="text-link" to="/register/rider">
              Register as rider
            </Link>
            <Link className="text-link" to="/register/driver">
              Register as driver
            </Link>
          </div>
        </div>
        <div className="public-shell__health">
          <h2>Platform health</h2>
          {healthQuery.isLoading ? <LoadingIndicator label="Checking backend status..." /> : null}
          {healthQuery.data ? (
            <dl className="status-grid">
              <div>
                <dt>Application</dt>
                <dd>{healthQuery.data.application}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{healthQuery.data.status}</dd>
              </div>
              <div>
                <dt>Database</dt>
                <dd>{healthQuery.data.database?.status ?? "Unknown"}</dd>
              </div>
            </dl>
          ) : null}
        </div>
      </section>
      <section className="public-shell__content">
        <Outlet />
      </section>
    </div>
  );
}
