import { useQuery } from "@tanstack/react-query";

import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import { getTripPayment } from "services/paymentService";
import { listRides } from "services/rideService";
import { formatDateTime, formatStatusLabel, getRideDisplayStatus, isRideActive, sortRidesByRequestedAt } from "utils/app";

export function RideHistoryPage() {
  const ridesQuery = useQuery({
    queryKey: ["rides"],
    queryFn: listRides
  });

  if (ridesQuery.isLoading) {
    return <LoadingIndicator label="Loading ride history..." />;
  }

  if (ridesQuery.isError) {
    return <ErrorDisplay message="Unable to load ride history." onAction={() => ridesQuery.refetch()} />;
  }

  const historicalRides = sortRidesByRequestedAt((ridesQuery.data ?? []).filter((ride) => !isRideActive(ride)));

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Ride history</p>
          <h1>Review completed rides, cancellations, and payment outcomes.</h1>
        </div>
      </div>

      <div className="list">
        {historicalRides.length === 0 ? <p className="empty-state">No completed or cancelled rides yet.</p> : null}
        {historicalRides.map((ride) => (
          <article className="list__card" key={ride.id}>
            <div className="list__card-header">
              <div>
                <h2>{ride.destination_address}</h2>
                <p>{formatDateTime(ride.updated_at)}</p>
              </div>
              <StatusBadge status={getRideDisplayStatus(ride)} />
            </div>
            <div className="list__meta">
              <span>Pickup: {ride.pickup_address}</span>
              <span>Estimated: {ride.estimated_distance} km / {ride.estimated_duration} min</span>
            </div>
            <div className="ride-summary">
              <div className="ride-summary__row">
                <span>Ride request ID</span>
                <strong className="code-chip">{ride.id}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Driver reference</span>
                <strong className="code-chip">{ride.trip?.driver_id ?? ride.driver_id ?? "Not assigned"}</strong>
              </div>
            </div>
            {ride.trip?.status === "TRIP_COMPLETED" ? <RidePaymentSummary tripId={ride.trip.id} /> : null}
          </article>
        ))}
      </div>
    </section>
  );
}

function RidePaymentSummary({ tripId }: { tripId: string }) {
  const paymentQuery = useQuery({
    queryKey: ["trip-payment", tripId],
    queryFn: () => getTripPayment(tripId),
    retry: 0
  });

  if (paymentQuery.isLoading) {
    return <p className="inline-muted">Loading payment...</p>;
  }

  if (paymentQuery.isError || !paymentQuery.data) {
    return <p className="inline-muted">Payment details are not available.</p>;
  }

  return (
    <div className="ride-summary ride-summary--compact">
      <div className="ride-summary__row">
        <span>Payment status</span>
        <strong>{formatStatusLabel(paymentQuery.data.status)}</strong>
      </div>
      <div className="ride-summary__row">
        <span>Amount</span>
        <strong>
          {paymentQuery.data.amount ?? "Pending"} {paymentQuery.data.currency ?? ""}
        </strong>
      </div>
      <div className="ride-summary__row">
        <span>Reference</span>
        <strong className="code-chip">{paymentQuery.data.payment_reference ?? "Not issued yet"}</strong>
      </div>
    </div>
  );
}
