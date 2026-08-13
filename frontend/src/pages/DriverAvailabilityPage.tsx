import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getErrorMessage } from "api/client";
import { Button } from "components/Button";
import { ConfirmationDialog } from "components/ConfirmationDialog";
import { ErrorDisplay } from "components/ErrorDisplay";
import { Form } from "components/Form";
import { LoadingIndicator } from "components/LoadingIndicator";
import { getMyDriverAvailability, updateMyDriverAvailability } from "services/availabilityService";
import type { DriverAvailabilityPayload } from "types/models";
import { validateDriverCoordinates } from "utils/app";
import { findAreaSelectionByCoordinates, formatAreaAddress, getAreaById, getAreasForCity, locationCities } from "utils/locations";

export function DriverAvailabilityPage() {
  const queryClient = useQueryClient();
  const [pendingPayload, setPendingPayload] = useState<DriverAvailabilityPayload | null>(null);
  const [form, setForm] = useState<DriverAvailabilityPayload>({
    status: "AVAILABLE",
    latitude: 40.7128,
    longitude: -74.006
  });
  const [locationForm, setLocationForm] = useState({
    city_id: "new-york-city",
    area_id: "manhattan"
  });
  const [error, setError] = useState("");

  const availabilityQuery = useQuery({
    queryKey: ["driver-availability", "me"],
    queryFn: getMyDriverAvailability
  });

  useEffect(() => {
    if (availabilityQuery.data) {
      const matchedArea = findAreaSelectionByCoordinates(availabilityQuery.data.latitude, availabilityQuery.data.longitude);
      setForm({
        status: availabilityQuery.data.status === "OFFLINE" ? "OFFLINE" : "AVAILABLE",
        latitude: availabilityQuery.data.latitude,
        longitude: availabilityQuery.data.longitude
      });
      setLocationForm({
        city_id: matchedArea.cityId,
        area_id: matchedArea.areaId
      });
    }
  }, [availabilityQuery.data]);

  const mutation = useMutation({
    mutationFn: updateMyDriverAvailability,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["driver-availability"] });
      queryClient.invalidateQueries({ queryKey: ["driver-trips"] });
      setPendingPayload(null);
    }
  });

  const selectedArea = getAreaById(locationForm.city_id, locationForm.area_id);

  if (availabilityQuery.isLoading) {
    return <LoadingIndicator label="Loading availability controls..." />;
  }

  if (availabilityQuery.isError) {
    return <ErrorDisplay message="Unable to load your availability." onAction={() => availabilityQuery.refetch()} />;
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedArea) {
      setError("Select a valid city and local area.");
      return;
    }
    const payload = {
      ...form,
      latitude: selectedArea.latitude,
      longitude: selectedArea.longitude
    };
    const validationError = validateDriverCoordinates(payload);

    if (validationError) {
      setError(validationError);
      return;
    }

    setPendingPayload(payload);
    setError("");
  }

  function confirmUpdate() {
    if (!pendingPayload) {
      return;
    }

    mutation.mutate(pendingPayload, {
      onError: (mutationError) => setError(getErrorMessage(mutationError))
    });
  }

  function stageStatus(status: DriverAvailabilityPayload["status"]) {
    if (!selectedArea) {
      setError("Select a valid city and local area.");
      return;
    }
    const payload = { ...form, status, latitude: selectedArea.latitude, longitude: selectedArea.longitude };
    const validationError = validateDriverCoordinates(payload);

    if (validationError) {
      setError(validationError);
      return;
    }

    setPendingPayload(payload);
    setError("");
  }

  return (
    <section className="page">
      <div className="stats-grid">
        <article className="stat-card">
          <span>Current status</span>
          <strong>{availabilityQuery.data?.status ?? "Unavailable"}</strong>
          <p>Select a city and local area to place the driver in a supported service zone.</p>
        </article>
        <article className="stat-card">
          <span>Quick actions</span>
          <strong>Dispatch controls</strong>
          <p>Use the buttons below to go AVAILABLE or OFFLINE with the selected service area.</p>
        </article>
      </div>

      <div className="panel">
        <div className="panel__actions">
          <Button onClick={() => stageStatus("AVAILABLE")} type="button">
            Go available
          </Button>
          <Button onClick={() => stageStatus("OFFLINE")} type="button" variant="ghost">
            Go offline
          </Button>
        </div>
      </div>

      <Form
        actions={
          <Button fullWidth type="submit" variant="primary">
            Review manual update
          </Button>
        }
        onSubmit={submit}
        subtitle="Only `OFFLINE` and `AVAILABLE` are accepted through the driver self-service API."
        title="Driver availability"
      >
        <label className="field">
          <span className="field__label">Status</span>
          <select
            className="input"
            onChange={(event) => setForm({ ...form, status: event.target.value as DriverAvailabilityPayload["status"] })}
            value={form.status}
          >
            <option value="AVAILABLE">Available</option>
            <option value="OFFLINE">Offline</option>
          </select>
        </label>
        <div className="grid-two">
          <label className="field">
            <span className="field__label">City</span>
            <select className="input" onChange={(event) => setLocationForm({ city_id: event.target.value, area_id: getAreasForCity(event.target.value)[0]?.areaId ?? "" })} value={locationForm.city_id}>
              {locationCities.map((city) => (
                <option key={city.id} value={city.id}>
                  {city.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field">
            <span className="field__label">Local area</span>
            <select className="input" onChange={(event) => setLocationForm({ ...locationForm, area_id: event.target.value })} value={locationForm.area_id}>
              {getAreasForCity(locationForm.city_id).map((area) => (
                <option key={area.areaId} value={area.areaId}>
                  {area.areaName}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="panel">
          <div className="ride-summary">
            <div className="ride-summary__row">
              <span>Selected location</span>
              <strong>{selectedArea ? formatAreaAddress(selectedArea) : "Select a local area"}</strong>
            </div>
            <div className="ride-summary__row">
              <span>Coordinates used by backend</span>
              <strong>
                {selectedArea?.latitude}, {selectedArea?.longitude}
              </strong>
            </div>
          </div>
        </div>
        {error ? <ErrorDisplay message={error} title="Update failed" /> : null}
      </Form>

      <ConfirmationDialog
        confirmLabel="Apply availability"
        confirmVariant="primary"
        isOpen={Boolean(pendingPayload)}
        isSubmitting={mutation.isPending}
        message="This will update your dispatch status and latest coordinates."
        onCancel={() => setPendingPayload(null)}
        onConfirm={confirmUpdate}
        title="Apply driver availability update?"
      />
    </section>
  );
}
