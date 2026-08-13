import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import { listMyDriverTrips } from "services/tripService";
import { formatDateTime, getDriverCompletedTrips } from "utils/app";

export function DriverTripHistoryPage() {
  const tripsQuery = useQuery({
    queryKey: ["driver-trips", "me"],
    queryFn: listMyDriverTrips
  });

  if (tripsQuery.isLoading) {
    return <LoadingIndicator label="Loading completed trips..." />;
  }

  if (tripsQuery.isError) {
    return <ErrorDisplay message="Unable to load completed trips." onAction={() => tripsQuery.refetch()} />;
  }

  const completedTrips = getDriverCompletedTrips(tripsQuery.data ?? []);

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Driver trip history</p>
          <h1>Review completed trips fetched from the driver trip API.</h1>
        </div>
      </div>

      <div className="list">
        {completedTrips.length === 0 ? <p className="empty-state">No completed trips are available for this driver yet.</p> : null}
        {completedTrips.map((trip) => (
          <article className="list__card" key={trip.id}>
            <div className="list__card-header">
              <div>
                <h2>{trip.ride_request.pickup_address}</h2>
                <p>Completed {formatDateTime(trip.completed_at)}</p>
              </div>
              <StatusBadge status={trip.status} />
            </div>
            <div className="list__meta">
              <span>Destination: {trip.ride_request.destination_address}</span>
              <span>
                Actual: {trip.actual_distance ?? "Pending"} km / {trip.actual_duration ?? "Pending"} min
              </span>
            </div>
            <div className="panel__actions">
              <Link className="button button--ghost" to={`/driver/current-trip/${trip.id}`}>
                Open trip details
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
