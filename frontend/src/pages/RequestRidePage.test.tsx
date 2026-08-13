import { fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { RequestRidePage } from "./RequestRidePage";
import { renderWithProviders } from "../test/renderWithProviders";

const navigateMock = vi.fn();

const { createRide, listRides } = vi.hoisted(() => ({
  createRide: vi.fn(),
  listRides: vi.fn()
}));

vi.mock("services/rideService", () => ({
  createRide,
  listRides
}));

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock
  };
});

describe("RequestRidePage", () => {
  afterEach(() => {
    navigateMock.mockReset();
    vi.clearAllMocks();
  });

  it("submits a ride request and navigates to the current ride view", async () => {
    listRides.mockResolvedValue([]);
    createRide.mockResolvedValue({ id: "ride-1" });

    renderWithProviders(<RequestRidePage />, { route: "/rider/request-ride" });

    fireEvent.change(await screen.findByLabelText("Pickup city"), { target: { value: "new-york-city" } });
    fireEvent.change(screen.getByLabelText("Pickup area"), { target: { value: "manhattan" } });
    fireEvent.change(screen.getByLabelText("Destination city"), { target: { value: "new-york-city" } });
    fireEvent.change(screen.getByLabelText("Destination area"), { target: { value: "brooklyn" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit ride request" }));

    await waitFor(() => {
      expect(createRide.mock.calls[0]?.[0]).toEqual(
        expect.objectContaining({
          pickup_address: "Manhattan, New York City",
          destination_address: "Brooklyn, New York City",
          ride_type: "STANDARD"
        })
      );
    });
    await waitFor(() => {
      expect(navigateMock).toHaveBeenCalledWith("/rider/current-ride");
    });
  });

  it("shows an error when the ride request fails", async () => {
    listRides.mockResolvedValue([]);
    createRide.mockRejectedValue({
      isAxiosError: true,
      message: "Request failed.",
      response: {
        data: {
          detail: "Pickup and destination cannot be identical."
        }
      }
    });

    renderWithProviders(<RequestRidePage />, { route: "/rider/request-ride" });

    fireEvent.change(await screen.findByLabelText("Pickup city"), { target: { value: "new-york-city" } });
    fireEvent.change(screen.getByLabelText("Pickup area"), { target: { value: "manhattan" } });
    fireEvent.change(screen.getByLabelText("Destination city"), { target: { value: "new-york-city" } });
    fireEvent.change(screen.getByLabelText("Destination area"), { target: { value: "manhattan" } });
    fireEvent.click(screen.getByRole("button", { name: "Submit ride request" }));

    expect(await screen.findByText("Pickup and destination cannot be identical.")).toBeInTheDocument();
  });
});
