import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { StatusBadge } from "components/StatusBadge";
import { getMyDriverAvailability } from "services/availabilityService";
import { acceptDriverRideOffer, listDriverRideOffers } from "services/rideService";
import { listMyDriverTrips } from "services/tripService";
import {
  formatDateTime,
  formatRelativeCount,
  getDriverCompletedTrips,
  getDriverCurrentTrip,
  shouldShowDriverDestination
} from "utils/app";
import { findAreaSelectionByCoordinates, formatAreaAddress } from "utils/locations";

export function DriverDashboardPage() {
  const queryClient = useQueryClient();
  const availabilityQuery = useQuery({
    queryKey: ["driver-availability", "me"],
    queryFn: getMyDriverAvailability,
    refetchInterval: 5000
  });

  const tripsQuery = useQuery({
    queryKey: ["driver-trips", "me"],
    queryFn: listMyDriverTrips,
    refetchInterval: 5000
  });

  const rideOffersQuery = useQuery({
    queryKey: ["driver-ride-offers", "me"],
    queryFn: listDriverRideOffers,
    refetchInterval: 5000
  });

  const acceptOfferMutation = useMutation({
    mutationFn: acceptDriverRideOffer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["driver-ride-offers"] });
      queryClient.invalidateQueries({ queryKey: ["driver-trips"] });
      queryClient.invalidateQueries({ queryKey: ["rides"] });
      queryClient.invalidateQueries({ queryKey: ["driver-availability"] });
    }
  });

  if (availabilityQuery.isLoading || tripsQuery.isLoading || rideOffersQuery.isLoading) {
    return <LoadingIndicator label="Loading driver workspace..." />;
  }

  if (availabilityQuery.isError) {
    return <ErrorDisplay message="Unable to load driver availability." onAction={() => availabilityQuery.refetch()} />;
  }

  if (tripsQuery.isError) {
    return <ErrorDisplay message="Unable to load driver trips." onAction={() => tripsQuery.refetch()} />;
  }

  if (rideOffersQuery.isError) {
    return <ErrorDisplay message="Unable to load ride offers." onAction={() => rideOffersQuery.refetch()} />;
  }

  const availability = availabilityQuery.data;
  if (!availability) {
    return <ErrorDisplay message="Availability data is unavailable." onAction={() => availabilityQuery.refetch()} />;
  }

  const trips = tripsQuery.data ?? [];
  const rideOffers = rideOffersQuery.data ?? [];
  const currentTrip = getDriverCurrentTrip(trips);
  const availabilityArea = findAreaSelectionByCoordinates(availability.latitude, availability.longitude);
  const completedTrips = getDriverCompletedTrips(trips);

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Driver dashboard</p>
          <h1>Manage availability and select a ride before moving it through each trip stage.</h1>
        </div>
        <Link className="button button--primary" to={currentTrip ? `/driver/current-trip/${currentTrip.id}` : "/driver/availability"}>
          {currentTrip ? "Open assigned ride" : "Update availability"}
        </Link>
      </div>

      <div className="stats-grid">
        <article className="stat-card">
          <span>Availability</span>
          <strong>{availability.status}</strong>
          <p>Last updated {formatDateTime(availability.updated_at)}.</p>
        </article>
        <article className="stat-card">
          <span>Assigned ride</span>
          <strong>{currentTrip ? currentTrip.status.replace(/_/g, " ") : "Awaiting selection"}</strong>
          <p>{currentTrip ? currentTrip.ride_request.pickup_address : "Go available and accept a ride offer from the queue."}</p>
        </article>
        <article className="stat-card">
          <span>Ride offers</span>
          <strong>{rideOffers.length}</strong>
          <p>{formatRelativeCount(rideOffers.length, "searching ride")} available for manual selection.</p>
        </article>
        <article className="stat-card">
          <span>Completed trips</span>
          <strong>{completedTrips.length}</strong>
          <p>{formatRelativeCount(completedTrips.length, "completed trip")} on record.</p>
        </article>
      </div>

      <div className="content-grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Availability controls</h2>
            <Link to="/driver/availability">Open controls</Link>
          </div>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Status</span>
              <StatusBadge status={availability.status} />
            </div>
            <div className="ride-summary__row">
              <span>Service area</span>
              <strong>{formatAreaAddress(availabilityArea)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Coordinates</span>
              <strong>
                {availability.latitude}, {availability.longitude}
              </strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Assigned ride</h2>
            <Link to={currentTrip ? `/driver/current-trip/${currentTrip.id}` : "/driver/current-trip"}>Open trip screen</Link>
          </div>
          {currentTrip ? (
            <div className="ride-summary">
              <div className="ride-summary__row">
                <span>Pickup</span>
                <strong>{currentTrip.ride_request.pickup_address}</strong>
              </div>
              <div className="ride-summary__row">
                <span>Destination</span>
                <strong>
                  {shouldShowDriverDestination(currentTrip.status)
                    ? currentTrip.ride_request.destination_address
                    : "Visible once the trip has started"}
                </strong>
              </div>
              <div className="ride-summary__row">
                <span>Status</span>
                <StatusBadge status={currentTrip.status} />
              </div>
            </div>
          ) : (
            <p className="empty-state">No ride is currently assigned to this driver. Review the ride offers below and accept one when ready.</p>
          )}
        </article>
      </div>

      <article className="panel">
        <div className="panel__header">
          <h2>Ride offers</h2>
          <span className="inline-muted">{rideOffers.length} nearby requests</span>
        </div>
        {rideOffers.length === 0 ? (
          <p className="empty-state">No matching ride requests are waiting right now. Keep your status set to AVAILABLE to receive new offers.</p>
        ) : (
          <div className="timeline">
            {rideOffers.map((offer) => (
              <div className="timeline__item" key={offer.id}>
                <div>
                  <strong>{offer.pickup_address}</strong>
                  <div className="inline-muted">To {offer.destination_address} | {offer.estimated_distance} km | {offer.estimated_duration} min</div>
                </div>
                <Button
                  isLoading={acceptOfferMutation.isPending && acceptOfferMutation.variables === offer.id}
                  onClick={() =>
                    acceptOfferMutation.mutate(offer.id, {
                      onError: () => {
                        rideOffersQuery.refetch();
                      }
                    })
                  }
                  type="button"
                >
                  Accept ride
                </Button>
              </div>
            ))}
          </div>
        )}
        {acceptOfferMutation.isError ? (
          <ErrorDisplay message={getErrorMessage(acceptOfferMutation.error)} title="Unable to accept ride" />
        ) : null}
      </article>
    </section>
  );
}
