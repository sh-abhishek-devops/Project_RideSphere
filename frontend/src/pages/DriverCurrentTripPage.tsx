import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { clearStoredDriverTripId, setStoredDriverTripId } from "api/authStorage";
import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { LoadingIndicator } from "components/LoadingIndicator";
import { Modal } from "components/Modal";
import { StatusBadge } from "components/StatusBadge";
import { completeTrip, getTrip, listMyDriverTrips, markTripArrived, markTripEnRoute, startTrip } from "services/tripService";
import type { Trip } from "types/models";
import { canTransitionDriverTrip, formatDateTime, formatStatusLabel, getDriverCurrentTrip, shouldShowDriverDestination } from "utils/app";

export function DriverCurrentTripPage() {
  const params = useParams<{ tripId?: string }>();
  const queryClient = useQueryClient();
  const [distance, setDistance] = useState("6.1");
  const [duration, setDuration] = useState("17");
  const [isPinModalOpen, setIsPinModalOpen] = useState(false);
  const [riderPinInput, setRiderPinInput] = useState("");
  const [error, setError] = useState("");

  const driverTripsQuery = useQuery({
    queryKey: ["driver-trips", "me"],
    queryFn: listMyDriverTrips,
    refetchInterval: 5000
  });

  const currentTripFromList = useMemo(() => getDriverCurrentTrip(driverTripsQuery.data ?? []), [driverTripsQuery.data]);
  const selectedTripId = params.tripId ?? currentTripFromList?.id ?? "";

  const tripQuery = useQuery({
    queryKey: ["trip", selectedTripId],
    queryFn: () => getTrip(selectedTripId),
    enabled: Boolean(selectedTripId),
    refetchInterval: 5000
  });

  useEffect(() => {
    if (currentTripFromList) {
      setStoredDriverTripId(currentTripFromList.id);
    } else if (!params.tripId) {
      clearStoredDriverTripId();
    }
  }, [currentTripFromList, params.tripId]);

  const transitionMutation = useMutation({
    mutationFn: async (action: "en-route" | "arrived" | "start" | "complete") => {
      if (!selectedTripId) {
        throw new Error("Trip ID is required.");
      }

      switch (action) {
        case "en-route":
          return markTripEnRoute(selectedTripId);
        case "arrived":
          return markTripArrived(selectedTripId);
        case "start":
          return startTrip(selectedTripId, { rider_start_pin: riderPinInput });
        case "complete":
          return completeTrip(selectedTripId, {
            actual_distance: Number(distance),
            actual_duration: Number(duration)
          });
      }
    },
    onSuccess: (trip) => {
      setStoredDriverTripId(trip.id);
      queryClient.invalidateQueries({ queryKey: ["trip", trip.id] });
      queryClient.invalidateQueries({ queryKey: ["driver-trips"] });
      queryClient.invalidateQueries({ queryKey: ["driver-availability"] });
    }
  });

  function runTransition(action: "en-route" | "arrived" | "start" | "complete", trip: Trip) {
    if (!canTransitionDriverTrip(trip.status, action)) {
      setError(`Trip cannot be moved to ${formatStatusLabel(action)} from ${formatStatusLabel(trip.status)}.`);
      return;
    }

    if (action === "complete" && (Number(distance) <= 0 || Number(duration) <= 0)) {
      setError("Actual distance and duration must be greater than zero.");
      return;
    }

    if (action === "start") {
      setError("");
      setRiderPinInput("");
      setIsPinModalOpen(true);
      return;
    }

    setError("");
    transitionMutation.mutate(action, {
      onError: (mutationError) => setError(getErrorMessage(mutationError))
    });
  }

  function confirmTripStart() {
    if (!/^\d{6}$/.test(riderPinInput)) {
      setError("Enter the 6-digit rider PIN before starting the trip.");
      return;
    }

    setError("");
    transitionMutation.mutate("start", {
      onError: (mutationError) => setError(getErrorMessage(mutationError)),
      onSuccess: () => {
        setIsPinModalOpen(false);
        setRiderPinInput("");
      }
    });
  }

  if (driverTripsQuery.isLoading) {
    return <LoadingIndicator label="Loading assigned ride..." />;
  }

  if (driverTripsQuery.isError) {
    return <ErrorDisplay message="Unable to load driver trips." onAction={() => driverTripsQuery.refetch()} />;
  }

  if (!selectedTripId) {
    return (
      <section className="page">
        <div className="panel empty-state">
          <h1>No assigned ride</h1>
          <p>The driver trip API has no active assignment for this account right now.</p>
          <div className="panel__actions">
            <Link className="button button--primary" to="/driver/availability">
              Go available
            </Link>
            <Link className="button button--ghost" to="/driver/history">
              View completed trips
            </Link>
          </div>
        </div>
      </section>
    );
  }

  if (tripQuery.isLoading) {
    return <LoadingIndicator label="Loading trip details..." />;
  }

  if (tripQuery.isError || !tripQuery.data) {
    return <ErrorDisplay message="Unable to load this trip." onAction={() => tripQuery.refetch()} />;
  }

  const trip = tripQuery.data;

  return (
    <section className="page">
      <div className="page__header">
        <div>
          <p className="eyebrow">Driver current trip</p>
          <h1>Advance the assigned ride through pickup, trip start, and completion.</h1>
        </div>
        <StatusBadge status={trip.status} />
      </div>

      <div className="content-grid">
        <article className="panel">
          <div className="panel__header">
            <h2>Assigned ride</h2>
            <span className="inline-muted">{formatStatusLabel(trip.ride_request.ride_type)}</span>
          </div>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Trip ID</span>
              <strong className="code-chip">{trip.id}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Ride request ID</span>
              <strong className="code-chip">{trip.ride_request_id}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Pickup location</span>
              <strong>{trip.ride_request.pickup_address}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Destination</span>
              <strong>
                {shouldShowDriverDestination(trip.status)
                  ? trip.ride_request.destination_address
                  : "Visible once the trip has started"}
              </strong>
            </div>
            <div className="ride-summary__row">
              <span>Vehicle reference</span>
              <strong className="code-chip">{trip.vehicle_id ?? "Vehicle not assigned"}</strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <h2>Trip actions</h2>
          <div className="action-grid">
            <Button
              disabled={!canTransitionDriverTrip(trip.status, "en-route")}
              isLoading={transitionMutation.isPending}
              onClick={() => runTransition("en-route", trip)}
              type="button"
            >
              Mark en route
            </Button>
            <Button
              disabled={!canTransitionDriverTrip(trip.status, "arrived")}
              isLoading={transitionMutation.isPending}
              onClick={() => runTransition("arrived", trip)}
              type="button"
              variant="secondary"
            >
              Mark arrived
            </Button>
            <Button
              disabled={!canTransitionDriverTrip(trip.status, "start")}
              isLoading={transitionMutation.isPending}
              onClick={() => runTransition("start", trip)}
              type="button"
              variant="secondary"
            >
              Start trip
            </Button>
          </div>

          <div className="complete-form">
            <label className="field">
              <span className="field__label">Actual distance (km)</span>
              <input
                className="input"
                min="0.1"
                onChange={(event) => setDistance(event.target.value)}
                step="0.1"
                type="number"
                value={distance}
              />
            </label>
            <label className="field">
              <span className="field__label">Actual duration (minutes)</span>
              <input
                className="input"
                min="1"
                onChange={(event) => setDuration(event.target.value)}
                step="1"
                type="number"
                value={duration}
              />
            </label>
            <Button
              disabled={!canTransitionDriverTrip(trip.status, "complete")}
              isLoading={transitionMutation.isPending}
              onClick={() => runTransition("complete", trip)}
              type="button"
              variant="primary"
            >
              Complete trip
            </Button>
          </div>
        </article>
      </div>

      <div className="content-grid">
        <article className="panel">
          <h2>Trip timing</h2>
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Started</span>
              <strong>{formatDateTime(trip.started_at)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Completed</span>
              <strong>{formatDateTime(trip.completed_at)}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Actual trip</span>
              <strong>
                {trip.actual_distance ?? "Pending"} km / {trip.actual_duration ?? "Pending"} min
              </strong>
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel__header">
            <h2>Status history</h2>
            <Link to="/driver/history">Completed trips</Link>
          </div>
          <div className="timeline">
            {trip.status_history.map((item) => (
              <div className="timeline__item" key={item.id}>
                <StatusBadge status={item.new_status} />
                <span>{formatDateTime(item.timestamp)}</span>
              </div>
            ))}
          </div>
        </article>
      </div>

      {error ? <ErrorDisplay message={error} title="Trip action failed" /> : null}

      <Modal
        footer={
          <>
            <Button onClick={() => setIsPinModalOpen(false)} type="button" variant="ghost">
              Cancel
            </Button>
            <Button isLoading={transitionMutation.isPending} onClick={confirmTripStart} type="button" variant="primary">
              Verify and start
            </Button>
          </>
        }
        isOpen={isPinModalOpen}
        onClose={() => setIsPinModalOpen(false)}
        title="Verify rider PIN"
      >
        <div className="field">
          <span className="field__label">Enter the rider's 6-digit start PIN</span>
          <input
            className="input"
            inputMode="numeric"
            maxLength={6}
            onChange={(event) => setRiderPinInput(event.target.value.replace(/\D/g, "").slice(0, 6))}
            placeholder="6-digit PIN"
            type="text"
            value={riderPinInput}
          />
          <span className="field__hint">Ask the rider for the PIN shown in their current ride screen.</span>
        </div>
      </Modal>
    </section>
  );
}
