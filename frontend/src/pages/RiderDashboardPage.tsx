import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";

import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import { listRides } from "services/rideService";
import { formatDateTime, formatRelativeCount, formatStatusLabel, getActiveRide, getRideDisplayStatus, sortRidesByRequestedAt } from "utils/app";

export function RiderDashboardPage() {
  const ridesQuery = useQuery({
    queryKey: ["rides"],
    queryFn: listRides,
    refetchInterval: 5000
  });

  if (ridesQuery.isLoading) {
    return <LoadingIndicator label="Loading your rider workspace..." />;
  }

  if (ridesQuery.isError) {
    return <ErrorDisplay message="Unable to load your rides." onAction={() => ridesQuery.refetch()} />;
  }

  const rides = sortRidesByRequestedAt(ridesQuery.data ?? []);
  const activeRide = getActiveRide(rides);
  const completedTrips = rides.filter((ride) => ride.trip?.status === "TRIP_COMPLETED").length;
  const lastCompletedRide = rides.find((ride) => ride.trip?.status === "TRIP_COMPLETED") ?? null;

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Rider dashboard</p>
          <h1>Monitor current trip progress and recent ride outcomes.</h1>
        </div>
        <Link className="button button--primary" to={activeRide ? "/rider/current-ride" : "/rider/request-ride"}>
          {activeRide ? "Open current ride" : "Request a ride"}
        </Link>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span>Total rides</span>
          <strong>{rides.length}</strong>
          <p>{formatRelativeCount(rides.length, "request")} recorded.</p>
        </article>
        <article className="stat-card">
          <span>Current flow state</span>
          <strong>{activeRide ? formatStatusLabel(getRideDisplayStatus(activeRide)) : "Ready"}</strong>
          <p>{activeRide ? activeRide.destination_address : "No ride is currently in progress."}</p>
        </article>
        <article className="stat-card">
          <span>Completed trips</span>
          <strong>{completedTrips}</strong>
          <p>{lastCompletedRide ? `Last completion ${formatDateTime(lastCompletedRide.updated_at)}` : "No completed trips yet."}</p>
        </article>
      </div>

      <div className="content-grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Current ride</h2>
            <Link to={activeRide ? "/rider/current-ride" : "/rider/request-ride"}>{activeRide ? "Open live view" : "Request now"}</Link>
          </div>
          {activeRide ? (
            <div className="ride-summary">
              <div className="ride-summary__row">
                <span>Pickup</span>
                <strong>{activeRide.pickup_address}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Destination</span>
                <strong>{activeRide.destination_address}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Status</span>
                <StatusBadge status={getRideDisplayStatus(activeRide)} />
              </div>
              <div className="ride-summary__row">
                <span>Driver reference</span>
                <strong className="code-chip">{activeRide.trip?.driver_id ?? activeRide.driver_id ?? "Searching..."}</strong>
              </div>
            </div>
          ) : (
            <p className="empty-state">No active ride is in progress. The request form is ready when you are.</p>
          )}
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Recent rides</h2>
            <Link to="/rider/history">View history</Link>
          </div>
          <div className="list">
            {rides.slice(0, 4).map((ride) => (
              <div className="list__item" key={ride.id}>
                <div>
                  <strong>{ride.destination_address}</strong>
                  <span>{formatDateTime(ride.created_at)}</span>
                </div>
                <StatusBadge status={getRideDisplayStatus(ride)} />
              </div>
            ))}
            {rides.length === 0 ? <p className="empty-state">No ride requests have been created yet.</p> : null}
          </div>
        </article>
      </div>
    </section>
  );
}
