import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import { getSupportInvestigation } from "services/supportCaseService";
import { formatDateTime, formatStatusLabel } from "utils/app";

export function RideInvestigationPage() {
  const { caseId = "" } = useParams();
  const investigationQuery = useQuery({
    queryKey: ["support-investigation", caseId],
    queryFn: () => getSupportInvestigation(caseId),
    enabled: Boolean(caseId)
  });

  if (investigationQuery.isLoading) {
    return <LoadingIndicator label="Loading ride investigation..." />;
  }

  if (investigationQuery.isError || !investigationQuery.data) {
    return <ErrorDisplay message="Unable to load the ride investigation." onAction={() => investigationQuery.refetch()} />;
  }

  const investigation = investigationQuery.data;

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Ride investigation</p>
          <h1>{investigation.case.issue_summary}</h1>
          <p className="inline-muted">Case ID {investigation.case.id}</p>
        </div>
        <StatusBadge status={investigation.case.status} />
      </div>

      <div className="content-grid">
        <article className="panel">
          <h2>Rider</h2>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Name</span>
              <strong>
                {investigation.rider.user.first_name} {investigation.rider.user.last_name}
              </strong>
            </div>
            <div className="ride-summary__row">
              <span>Email</span>
              <strong>{investigation.rider.user.email}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Phone</span>
              <strong>{investigation.rider.user.phone_number}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Driver and vehicle</h2>
          {investigation.driver ? (
            <div className="ride-summary">
              <div className="ride-summary__row">
                <span>Driver</span>
                <strong>
                  {investigation.driver.user.first_name} {investigation.driver.user.last_name}
                </strong>
              </div>
              <div className="ride-summary__row">
                <span>Email</span>
                <strong>{investigation.driver.user.email}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Vehicle</span>
                <strong>
                  {investigation.vehicle
                    ? `${investigation.vehicle.color} ${investigation.vehicle.make} ${investigation.vehicle.model}`
                    : "No active vehicle attached"}
                </strong>
              </div>
              <div className="ride-summary__row">
                <span>License plate</span>
                <strong>{investigation.vehicle?.license_plate ?? "Unavailable"}</strong>
              </div>
            </div>
          ) : (
            <p className="empty-state">No driver has been linked to this ride request.</p>
          )}
        </article>
      </div>

      <div className="content-grid">
        <article className="panel">
          <h2>Ride request</h2>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Status</span>
              <StatusBadge status={investigation.ride_request.trip?.status ?? investigation.ride_request.status} />
            </div>
            <div className="ride-summary__row">
              <span>Pickup</span>
              <strong>{investigation.ride_request.pickup_address}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Destination</span>
              <strong>{investigation.ride_request.destination_address}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Requested</span>
              <strong>{formatDateTime(investigation.ride_request.requested_at)}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Trip and payment</h2>
          {investigation.trip ? (
            <div className="ride-summary">
              <div className="ride-summary__row">
                <span>Trip status</span>
                <StatusBadge status={investigation.trip.status} />
              </div>
              <div className="ride-summary__row">
                <span>Started</span>
                <strong>{formatDateTime(investigation.trip.started_at)}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Completed</span>
                <strong>{formatDateTime(investigation.trip.completed_at)}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Payment status</span>
                <strong>{investigation.payment ? formatStatusLabel(investigation.payment.status) : "No payment record"}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Payment details</span>
                <strong>{investigation.payment?.amount == null ? "Redacted for support role" : "Visible"}</strong>
              </div>
            </div>
          ) : (
            <p className="empty-state">No trip is linked to this ride request yet.</p>
          )}
        </article>
      </div>

      <article className="panel">
        <div className="panel__header">
          <h2>Trip status timeline</h2>
          <Link to={`/support/cases/${investigation.case.id}`}>Open case details</Link>
        </div>
        {investigation.trip ? (
          <div className="timeline">
            {investigation.trip.status_history.map((item) => (
              <div className="timeline__item" key={item.id}>
                <StatusBadge status={item.new_status} />
                <span>{formatDateTime(item.timestamp)}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="empty-state">Timeline will appear once a trip exists for this ride request.</p>
        )}
      </article>
    </section>
  );
}
