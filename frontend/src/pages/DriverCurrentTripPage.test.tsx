import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Route, Routes } from "react-router-dom";

import { DriverCurrentTripPage } from "./DriverCurrentTripPage";
import { renderWithProviders } from "../test/renderWithProviders";

const { clearStoredDriverTripId, setStoredDriverTripId } = vi.hoisted(() => ({
  clearStoredDriverTripId: vi.fn(),
  setStoredDriverTripId: vi.fn()
}));
const { completeTrip, getTrip, listMyDriverTrips, markTripArrived, markTripEnRoute, startTrip } = vi.hoisted(() => ({
  completeTrip: vi.fn(),
  getTrip: vi.fn(),
  listMyDriverTrips: vi.fn(),
  markTripArrived: vi.fn(),
  markTripEnRoute: vi.fn(),
  startTrip: vi.fn()
}));

vi.mock("api/authStorage", () => ({
  clearStoredDriverTripId,
  setStoredDriverTripId,
  getStoredDriverTripId: () => ""
}));

vi.mock("services/tripService", () => ({
  completeTrip,
  getTrip,
  listMyDriverTrips,
  markTripArrived,
  markTripEnRoute,
  startTrip
}));

const assignedTrip = {
  id: "trip-1",
  ride_request_id: "ride-1",
  rider_id: "rider-1",
  driver_id: "driver-1",
  vehicle_id: "vehicle-1",
  status: "DRIVER_ASSIGNED" as const,
  rider_start_pin: null,
  started_at: null,
  completed_at: null,
  actual_distance: null,
  actual_duration: null,
  created_at: "2026-08-11T10:00:00Z",
  updated_at: "2026-08-11T10:00:00Z",
  ride_request: {
    id: "ride-1",
    pickup_address: "100 Main Street",
    pickup_latitude: 40.7128,
    pickup_longitude: -74.006,
    destination_address: "200 State Street",
    destination_latitude: 40.73,
    destination_longitude: -73.93,
    ride_type: "STANDARD" as const
  },
  status_history: [
    {
      id: "history-1",
      trip_id: "trip-1",
      previous_status: null,
      new_status: "DRIVER_ASSIGNED" as const,
      changed_by: "user-1",
      timestamp: "2026-08-11T10:00:00Z"
    }
  ]
};

describe("DriverCurrentTripPage", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("allows the driver to move an assigned trip to en route", async () => {
    listMyDriverTrips.mockResolvedValue([assignedTrip]);
    getTrip.mockResolvedValue(assignedTrip);
    markTripEnRoute.mockResolvedValue({ ...assignedTrip, status: "DRIVER_EN_ROUTE" });

    renderWithProviders(
      <Routes>
        <Route path="/driver/current-trip/:tripId" element={<DriverCurrentTripPage />} />
      </Routes>,
      { route: "/driver/current-trip/trip-1" }
    );

    fireEvent.click(await screen.findByRole("button", { name: "Mark en route" }));

    await waitFor(() => {
      expect(markTripEnRoute).toHaveBeenCalledWith("trip-1");
    });
  });

  it("requires rider PIN verification before starting a trip", async () => {
    const arrivedTrip = { ...assignedTrip, status: "DRIVER_ARRIVED" as const };
    listMyDriverTrips.mockResolvedValue([arrivedTrip]);
    getTrip.mockResolvedValue(arrivedTrip);
    startTrip.mockResolvedValue({ ...arrivedTrip, status: "TRIP_STARTED" as const });

    renderWithProviders(
      <Routes>
        <Route path="/driver/current-trip/:tripId" element={<DriverCurrentTripPage />} />
      </Routes>,
      { route: "/driver/current-trip/trip-1" }
    );

    fireEvent.click(await screen.findByRole("button", { name: "Start trip" }));
    fireEvent.change(screen.getByPlaceholderText("6-digit PIN"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Verify and start" }));

    await waitFor(() => {
      expect(startTrip).toHaveBeenCalledWith("trip-1", { rider_start_pin: "123456" });
    });
  });

  it("shows validation errors instead of sending an invalid completion payload", async () => {
    const startedTrip = { ...assignedTrip, status: "TRIP_STARTED" as const };
    listMyDriverTrips.mockResolvedValue([startedTrip]);
    getTrip.mockResolvedValue(startedTrip);

    renderWithProviders(
      <Routes>
        <Route path="/driver/current-trip/:tripId" element={<DriverCurrentTripPage />} />
      </Routes>,
      { route: "/driver/current-trip/trip-1" }
    );

    fireEvent.change(await screen.findByLabelText("Actual distance (km)"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Actual duration (minutes)"), { target: { value: "0" } });
    fireEvent.click(screen.getByRole("button", { name: "Complete trip" }));

    expect(await screen.findByText("Actual distance and duration must be greater than zero.")).toBeInTheDocument();
    expect(completeTrip).not.toHaveBeenCalled();
  });
});
