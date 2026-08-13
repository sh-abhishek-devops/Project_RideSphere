import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ErrorDisplay } from "components/ErrorDisplay";
import { Form } from "components/Form";
import { LoadingIndicator } from "components/LoadingIndicator";
import { createRide, listRides } from "services/rideService";
import type { RideType } from "types/models";
import { getActiveRide, getRideDisplayStatus } from "utils/app";
import { estimateDurationMinutes, formatAreaAddress, getAreaById, getAreasForCity, haversineKm, locationCities } from "utils/locations";

const initialForm = {
  pickup_city_id: "new-york-city",
  pickup_area_id: "manhattan",
  destination_city_id: "new-york-city",
  destination_area_id: "brooklyn",
  ride_type: "STANDARD" as RideType,
};

export function RequestRidePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [form, setForm] = useState(initialForm);
  const [error, setError] = useState("");

  const ridesQuery = useQuery({
    queryKey: ["rides"],
    queryFn: listRides,
    refetchInterval: 10000
  });

  const mutation = useMutation({
    mutationFn: createRide,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rides"] });
      navigate("/rider/current-ride");
    }
  });

  function updateField(field: keyof typeof form, value: string) {
    setForm((current) => {
      if (field === "pickup_city_id") {
        return {
          ...current,
          pickup_city_id: value,
          pickup_area_id: getAreasForCity(value)[0]?.areaId ?? ""
        };
      }

      if (field === "destination_city_id") {
        return {
          ...current,
          destination_city_id: value,
          destination_area_id: getAreasForCity(value)[0]?.areaId ?? ""
        };
      }

      return { ...current, [field]: value };
    });
  }

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");

    const pickupArea = getAreaById(form.pickup_city_id, form.pickup_area_id);
    const destinationArea = getAreaById(form.destination_city_id, form.destination_area_id);

    if (!pickupArea || !destinationArea) {
      setError("Select valid pickup and destination areas.");
      return;
    }

    const estimatedDistance = Number(haversineKm(
      pickupArea.latitude,
      pickupArea.longitude,
      destinationArea.latitude,
      destinationArea.longitude
    ).toFixed(1));
    const estimatedDuration = estimateDurationMinutes(estimatedDistance);

    mutation.mutate(
      {
        pickup_address: formatAreaAddress(pickupArea),
        pickup_latitude: pickupArea.latitude,
        pickup_longitude: pickupArea.longitude,
        destination_address: formatAreaAddress(destinationArea),
        destination_latitude: destinationArea.latitude,
        destination_longitude: destinationArea.longitude,
        ride_type: form.ride_type,
        estimated_distance: estimatedDistance,
        estimated_duration: estimatedDuration
      },
      {
        onError: (submissionError) => setError(getErrorMessage(submissionError))
      }
    );
  }

  if (ridesQuery.isLoading) {
    return <LoadingIndicator label="Loading ride request workspace..." />;
  }

  if (ridesQuery.isError) {
    return <ErrorDisplay message="Unable to prepare the ride request form." onAction={() => ridesQuery.refetch()} />;
  }

  const activeRide = getActiveRide(ridesQuery.data ?? []);

  if (activeRide) {
    return (
      <section className="page">
        <div className="panel empty-state">
          <h1>An active ride already exists</h1>
          <p>
            Ride status: <strong>{getRideDisplayStatus(activeRide).replace(/_/g, " ")}</strong>
          </p>
          <p>Finish or cancel the current ride before requesting another one.</p>
          <div className="panel__actions">
            <Link className="button button--primary" to="/rider/current-ride">
              Open current ride
            </Link>
            <Link className="button button--ghost" to="/rider/dashboard">
              Back to dashboard
            </Link>
          </div>
        </div>
      </section>
    );
  }

  const pickupArea = getAreaById(form.pickup_city_id, form.pickup_area_id);
  const destinationArea = getAreaById(form.destination_city_id, form.destination_area_id);
  const estimatedDistance =
    pickupArea && destinationArea
      ? Number(haversineKm(pickupArea.latitude, pickupArea.longitude, destinationArea.latitude, destinationArea.longitude).toFixed(1))
      : 0;
  const estimatedDuration = estimateDurationMinutes(estimatedDistance);

  return (
    <section className="page">
      <Form
        actions={
          <Button fullWidth isLoading={mutation.isPending} type="submit">
            Submit ride request
          </Button>
        }
        onSubmit={handleSubmit}
        subtitle="Enter the real pickup and destination details that will be sent to the RideSphere backend."
        title="Request a new ride"
      >
        <div className="grid-two">
          <label className="field">
            <span className="field__label">Pickup city</span>
            <select className="input" onChange={(event) => updateField("pickup_city_id", event.target.value)} value={form.pickup_city_id}>
              {locationCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field__label">Pickup area</span>
            <select className="input" onChange={(event) => updateField("pickup_area_id", event.target.value)} value={form.pickup_area_id}>
              {getAreasForCity(form.pickup_city_id).map((area) => (
                <option key={area.areaId} value={area.areaId}>
                  {area.areaName}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="grid-two">
          <label className="field">
            <span className="field__label">Destination city</span>
            <select className="input" onChange={(event) => updateField("destination_city_id", event.target.value)} value={form.destination_city_id}>
              {locationCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field__label">Destination area</span>
            <select className="input" onChange={(event) => updateField("destination_area_id", event.target.value)} value={form.destination_area_id}>
              {getAreasForCity(form.destination_city_id).map((area) => (
                <option key={area.areaId} value={area.areaId}>
                  {area.areaName}
                </option>
              ))}
            </select>
          </label>
        </div>
        <label className="field">
          <span className="field__label">Ride type</span>
          <select className="input" onChange={(event) => updateField("ride_type", event.target.value)} value={form.ride_type}>
            <option value="STANDARD">Standard</option>
            <option value="XL">XL</option>
            <option value="PREMIUM">Premium</option>
          </select>
        </label>
        <div className="panel">
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Pickup selection</span>
              <strong>{pickupArea ? formatAreaAddress(pickupArea) : "Select a pickup area"}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Destination selection</span>
              <strong>{destinationArea ? formatAreaAddress(destinationArea) : "Select a destination area"}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Estimated trip</span>
              <strong>
                {estimatedDistance} km / {estimatedDuration} min
              </strong>
            </div>
          </div>
        </div>
        {error ? <ErrorDisplay message={error} title="Request failed" /> : null}
      </Form>
    </section>
  );
}
