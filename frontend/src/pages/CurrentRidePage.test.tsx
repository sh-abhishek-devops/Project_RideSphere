import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CurrentRidePage } from "./CurrentRidePage";
import { renderWithProviders } from "../test/renderWithProviders";

const { getTripPayment } = vi.hoisted(() => ({
  getTripPayment: vi.fn()
}));
const { cancelRide, listRides } = vi.hoisted(() => ({
  cancelRide: vi.fn(),
  listRides: vi.fn()
}));

vi.mock("services/rideService", () => ({
  cancelRide,
  listRides
}));

vi.mock("services/paymentService", () => ({
  getTripPayment
}));

describe("CurrentRidePage", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("displays trip status milestones for an active trip", async () => {
    listRides.mockResolvedValue([
      {
        id: "ride-1",
        rider_id: "rider-1",
        driver_id: "driver-1",
        pickup_address: "100 Main Street",
        pickup_latitude: 40.7128,
        pickup_longitude: -74.006,
        destination_address: "200 State Street",
        destination_latitude: 40.73,
        destination_longitude: -73.93,
        ride_type: "STANDARD",
        requested_at: "2026-08-11T10:00:00Z",
        status: "DRIVER_ASSIGNED",
        estimated_distance: 7.5,
        estimated_duration: 18,
        created_at: "2026-08-11T10:00:00Z",
        updated_at: "2026-08-11T10:20:00Z",
        trip: {
          id: "trip-1",
          ride_request_id: "ride-1",
          rider_id: "rider-1",
          driver_id: "driver-1",
          vehicle_id: "vehicle-1",
          status: "TRIP_STARTED",
          started_at: "2026-08-11T10:05:00Z",
          completed_at: null,
          actual_distance: null,
          actual_duration: null,
          created_at: "2026-08-11T10:00:00Z",
          updated_at: "2026-08-11T10:20:00Z",
          ride_request: {
            id: "ride-1",
            pickup_address: "100 Main Street",
            pickup_latitude: 40.7128,
            pickup_longitude: -74.006,
            destination_address: "200 State Street",
            destination_latitude: 40.73,
            destination_longitude: -73.93,
            ride_type: "STANDARD"
          },
          status_history: [
            {
              id: "history-1",
              trip_id: "trip-1",
              previous_status: null,
              new_status: "DRIVER_ASSIGNED",
              changed_by: "user-1",
              timestamp: "2026-08-11T10:00:00Z"
            },
            {
              id: "history-2",
              trip_id: "trip-1",
              previous_status: "DRIVER_ARRIVED",
              new_status: "TRIP_STARTED",
              changed_by: "user-1",
              timestamp: "2026-08-11T10:10:00Z"
            }
          ]
        }
      }
    ]);

    renderWithProviders(<CurrentRidePage />, { route: "/rider/current-ride" });

    expect(await screen.findByText("Track the live rider journey from request through payment.")).toBeInTheDocument();
    expect(screen.getAllByText("Trip Started").length).toBeGreaterThan(0);
    expect(screen.getByText("200 State Street")).toBeInTheDocument();
  });

  it("shows a loading error when rides cannot be fetched", async () => {
    listRides.mockRejectedValue(new Error("network"));

    renderWithProviders(<CurrentRidePage />, { route: "/rider/current-ride" });

    expect(await screen.findByText("Unable to load current ride.")).toBeInTheDocument();
  });
});
