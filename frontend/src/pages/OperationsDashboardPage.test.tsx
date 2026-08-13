import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { OperationsDashboardPage } from "./OperationsDashboardPage";

const { getOperationsDashboardMetrics, fetchHealthStatus } = vi.hoisted(() => ({
  getOperationsDashboardMetrics: vi.fn(),
  fetchHealthStatus: vi.fn()
}));

vi.mock("services/operationsService", () => ({
  getOperationsDashboardMetrics
}));

vi.mock("services/healthService", () => ({
  fetchHealthStatus
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false
      }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <OperationsDashboardPage />
    </QueryClientProvider>
  );
}

describe("OperationsDashboardPage", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders aggregated metrics from the backend", async () => {
    fetchHealthStatus.mockResolvedValue({
      status: "healthy",
      application: "RideSphere",
      database: {
        status: "healthy",
        driver: "psycopg",
        engine: "postgresql",
        host: "localhost",
        port: 5432,
        database: "ridesphere"
      }
    });
    getOperationsDashboardMetrics.mockResolvedValue({
      date_from: "2026-08-10",
      date_to: "2026-08-11",
      total_ride_requests: 21,
      rides_searching_for_drivers: 3,
      active_trips: 5,
      completed_trips: 9,
      cancelled_rides: 4,
      available_drivers: 6,
      drivers_currently_on_trips: 2,
      payment_successes: 8,
      payment_failures: 1,
      open_support_cases: 2,
      generated_at: "2026-08-11T12:00:00Z"
    });

    renderPage();

    expect(await screen.findByText("Operations dashboard")).toBeInTheDocument();
    expect(await screen.findByText("21")).toBeInTheDocument();
    expect(screen.getByText("RideSphere")).toBeInTheDocument();
    expect(screen.getByText("2026-08-10")).toBeInTheDocument();
    expect(getOperationsDashboardMetrics).toHaveBeenCalledWith({ dateFrom: "", dateTo: "" });
  });

  it("shows a validation error for an invalid date range and does not refetch metrics", async () => {
    fetchHealthStatus.mockResolvedValue({
      status: "healthy",
      application: "RideSphere",
      database: {
        status: "healthy",
        driver: "psycopg",
        engine: "postgresql",
        host: "localhost",
        port: 5432,
        database: "ridesphere"
      }
    });
    getOperationsDashboardMetrics.mockResolvedValue({
      date_from: null,
      date_to: null,
      total_ride_requests: 0,
      rides_searching_for_drivers: 0,
      active_trips: 0,
      completed_trips: 0,
      cancelled_rides: 0,
      available_drivers: 0,
      drivers_currently_on_trips: 0,
      payment_successes: 0,
      payment_failures: 0,
      open_support_cases: 0,
      generated_at: "2026-08-11T12:00:00Z"
    });

    renderPage();
    await screen.findByText("Operations dashboard");

    fireEvent.change(screen.getByLabelText("Start date"), { target: { value: "2026-08-11" } });
    fireEvent.change(screen.getByLabelText("End date"), { target: { value: "2026-08-10" } });
    fireEvent.click(screen.getByRole("button", { name: "Apply filters" }));

    await waitFor(() => {
      expect(screen.getByText("End date must be on or after the start date.")).toBeInTheDocument();
    });
    expect(getOperationsDashboardMetrics).toHaveBeenCalledTimes(1);
  });
});
