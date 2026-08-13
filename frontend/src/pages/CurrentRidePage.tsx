import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ConfirmationDialog } from "components/ConfirmationDialog";
import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { Modal } from "components/Modal";
import { StatusBadge } from "components/StatusBadge";
import { getTripPayment } from "services/paymentService";
import { cancelRide, listRides } from "services/rideService";
import type { PaymentStatus, RideRequest } from "types/models";
import { canCancelRide, formatDateTime, formatStatusLabel, getActiveRide, getRideDisplayStatus } from "utils/app";

const riderFlowSteps = [
  "REQUESTED",
  "SEARCHING_DRIVER",
  "DRIVER_ASSIGNED",
  "DRIVER_EN_ROUTE",
  "DRIVER_ARRIVED",
  "TRIP_STARTED",
  "TRIP_COMPLETED"
] as const;

type RiderFlowStep = (typeof riderFlowSteps)[number];

export function CurrentRidePage() {
  const queryClient = useQueryClient();
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isSupportOpen, setIsSupportOpen] = useState(false);
  const [error, setError] = useState("");

  const ridesQuery = useQuery({
    queryKey: ["rides"],
    queryFn: listRides,
    refetchInterval: 5000
  });

  const activeRide = useMemo(() => getActiveRide(ridesQuery.data ?? []), [ridesQuery.data]);

  const paymentQuery = useQuery({
    queryKey: ["trip-payment", activeRide?.trip?.id],
    queryFn: () => getTripPayment(activeRide!.trip!.id),
    enabled: Boolean(activeRide?.trip?.id),
    retry: 0,
    refetchInterval: ({ state }) => {
      const paymentStatus = state.data?.status;
      return paymentStatus === "SUCCESS" || paymentStatus === "FAILED" || paymentStatus === "REFUNDED" ? false : 5000;
    }
  });

  const cancelMutation = useMutation({
    mutationFn: cancelRide,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rides"] });
      setIsConfirmOpen(false);
    }
  });

  if (ridesQuery.isLoading) {
    return <LoadingIndicator label="Loading current ride..." />;
  }

  if (ridesQuery.isError) {
    return <ErrorDisplay message="Unable to load current ride." onAction={() => ridesQuery.refetch()} />;
  }

  if (!activeRide) {
    return (
      <section className="page">
        <div className="panel empty-state">
          <h1>No active ride right now</h1>
          <p>Request a new ride to start real-time tracking.</p>
          <div className="panel__actions">
            <Link className="button button--primary" to="/rider/request-ride">
              Request a ride
            </Link>
            <Link className="button button--ghost" to="/rider/history">
              View completed rides
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const ride = activeRide;
  const rideStatus = getRideDisplayStatus(ride);
  const steps = buildRiderFlowSteps(ride, paymentQuery.data?.status);
  const showPaymentCard = rideStatus === "TRIP_COMPLETED" || Boolean(paymentQuery.data);
  const rideCanBeCancelled = canCancelRide(ride);

  function handleCancel() {
    setError("");
    cancelMutation.mutate(ride.id, {
      onError: (mutationError) => setError(getErrorMessage(mutationError))
    });
  }

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Current ride</p>
          <h1>Track the live rider journey from request through payment.</h1>
        </div>
        <StatusBadge status={rideStatus} />
      </div>

      <div className="content-grid">
        <article className="panel">
          <h2>Live status flow</h2>
          <div className="milestone-list">
            {steps.map((step) => (
              <div className={`milestone ${step.stateClass}`} key={step.label}>
                <div className="milestone__header">
                  <strong>{step.label}</strong>
                  <span>{step.stateLabel}</span>
                </div>
                <p>{step.description}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>Route overview</h2>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Requested</span>
              <strong>{formatDateTime(ride.requested_at)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Pickup</span>
              <strong>{ride.pickup_address}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Destination</span>
              <strong>{ride.destination_address}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Ride type</span>
              <strong>{formatStatusLabel(ride.ride_type)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Estimated trip</span>
              <strong>
                {ride.estimated_distance} km / {ride.estimated_duration} min
              </strong>
            </div>
          </div>
        </article>
      </div>

      <div className="content-grid">
        <article className="panel">
          <h2>Assignment details</h2>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Ride request ID</span>
              <strong className="code-chip">{ride.id}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Driver reference</span>
              <strong className="code-chip">{ride.trip?.driver_id ?? ride.driver_id ?? "Searching..."}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Vehicle reference</span>
              <strong className="code-chip">{ride.trip?.vehicle_id ?? "Assigned after dispatch"}</strong>
            </div>
          </div>
          <p className="inline-muted">
            Rider-facing driver and vehicle profile details are not exposed by the current backend yet, so the live view shows
            the assignment references returned by the authenticated rider endpoints.
          </p>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Trip history</h2>
          {ride.trip ? <span className="inline-muted">{ride.trip.status_history.length} updates</span> : null}
          </div>
          {ride.trip ? (
            <div className="timeline">
              {ride.trip.status_history.map((item) => (
                <div className="timeline__item" key={item.id}>
                  <StatusBadge status={item.new_status} />
                  <span>{formatDateTime(item.timestamp)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">RideSphere is searching for an available driver near the pickup location.</p>
          )}
        </article>
      </div>

      {showPaymentCard ? (
        <article className="panel">
          <div className="panel__header">
            <h2>Payment status</h2>
            {paymentQuery.data ? <StatusBadge status={paymentQuery.data.status} /> : null}
          </div>
          {paymentQuery.isLoading ? <LoadingIndicator label="Loading payment status..." /> : null}
          {paymentQuery.isError ? (
            <ErrorDisplay
              actionLabel="Refresh payment"
              message="Payment information is not available yet."
              onAction={() => paymentQuery.refetch()}
              title="Payment not ready"
            />
          ) : null}
          {paymentQuery.data ? (
            <div className="ride-summary">
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
              <div className="ride-summary__row">
                <span>Updated</span>
                <strong>{formatDateTime(paymentQuery.data.updated_at)}</strong>
              </div>
            </div>
          ) : null}
        </article>
      ) : null}

      <div className="panel panel--actions">
        <div>
          <h2>Actions</h2>
          <p className="inline-muted">Manage the current ride using the available rider controls.</p>
        </div>
        <div className="panel__actions">
          {rideCanBeCancelled ? (
            <Button onClick={() => setIsConfirmOpen(true)} type="button" variant="danger">
              Cancel ride
            </Button>
          ) : null}
          <Button onClick={() => setIsSupportOpen(true)} type="button" variant="secondary">
            Open support case
          </Button>
          <Link className="button button--ghost" to="/rider/history">
            View completed rides
          </Link>
        </div>
        {error ? <ErrorDisplay message={error} title="Unable to cancel ride" /> : null}
      </div>

      <ConfirmationDialog
        confirmLabel="Cancel ride"
        isOpen={isConfirmOpen}
        isSubmitting={cancelMutation.isPending}
        message="This will cancel the active ride request and release any assigned trip state."
        onCancel={() => setIsConfirmOpen(false)}
        onConfirm={handleCancel}
        title="Cancel current ride?"
      />

      <Modal
        footer={
          <Button onClick={() => setIsSupportOpen(false)} type="button" variant="primary">
            Close
          </Button>
        }
        isOpen={isSupportOpen}
        onClose={() => setIsSupportOpen(false)}
        title="Support case creation"
      >
        <p>
          The current backend does not expose a rider endpoint to create support cases yet. This frontend is connected only to
          live backend capabilities, so no support request is submitted from this screen.
        </p>
      </Modal>
    </section>
  );
}

function buildRiderFlowSteps(ride: RideRequest, paymentStatus?: PaymentStatus) {
  const currentStatus = getRideDisplayStatus(ride);
  const currentIndex = riderFlowSteps.indexOf(currentStatus as RiderFlowStep);

  return riderFlowSteps.map((step, index) => {
    const isComplete = currentIndex > index || (step === "TRIP_COMPLETED" && currentStatus === "TRIP_COMPLETED");
    const isCurrent = currentIndex === index;
    const stateClass = isCurrent ? "milestone--current" : isComplete ? "milestone--complete" : "milestone--upcoming";
    const stateLabel = isCurrent ? "Current" : isComplete ? "Completed" : "Pending";

    return {
      label: formatStatusLabel(step),
      description: getStepDescription(step, paymentStatus),
      stateClass,
      stateLabel
    };
  });
}

function getStepDescription(step: RiderFlowStep, paymentStatus?: PaymentStatus): string {
  switch (step) {
    case "REQUESTED":
      return "RideSphere accepted the request and stored the trip details.";
    case "SEARCHING_DRIVER":
      return "The platform is checking nearby available drivers.";
    case "DRIVER_ASSIGNED":
      return "A single driver has been reserved for this ride request.";
    case "DRIVER_EN_ROUTE":
      return "The assigned driver is heading toward the pickup point.";
    case "DRIVER_ARRIVED":
      return "The driver reported arrival at the pickup location.";
    case "TRIP_STARTED":
      return "The rider is on trip and operational tracking is active.";
    case "TRIP_COMPLETED":
      return paymentStatus ? `Trip completed. Payment is currently ${formatStatusLabel(paymentStatus)}.` : "Trip completed. Payment is being checked.";
    default:
      return "";
  }
}
