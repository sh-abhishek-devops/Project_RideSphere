import type {
  AvailabilityStatus,
  DriverAvailabilityPayload,
  PaymentStatus,
  RideRequest,
  RideRequestStatus,
  Trip,
  TripStatus,
  UserRole
} from "types/models";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "Not available";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short"
  }).format(new Date(value));
}

export function formatRelativeCount(value: number, noun: string): string {
  return `${value} ${noun}${value === 1 ? "" : "s"}`;
}

export function formatRole(role: UserRole): string {
  return role.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (match: string) => match.toUpperCase());
}

export function formatStatusLabel(
  status: RideRequestStatus | TripStatus | PaymentStatus | AvailabilityStatus | string
): string {
  return status.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (match: string) => match.toUpperCase());
}

export function getDefaultRouteForRole(role: UserRole): string {
  switch (role) {
    case "RIDER":
      return "/rider/dashboard";
    case "DRIVER":
      return "/driver/dashboard";
    case "SUPPORT_AGENT":
    case "PAYMENT_AGENT":
      return "/support/dashboard";
    case "OPERATIONS_MANAGER":
    case "ADMIN":
      return "/operations/dashboard";
    default:
      return "/unauthorized";
  }
}

export function isRideActive(ride: RideRequest): boolean {
  if (ride.status === "CANCELLED") {
    return false;
  }

  return ride.trip?.status !== "TRIP_COMPLETED" && ride.trip?.status !== "CANCELLED";
}

export function getRideDisplayStatus(ride: RideRequest): RideRequestStatus | TripStatus {
  return ride.trip?.status ?? ride.status;
}

export function getActiveRide(rides: RideRequest[]): RideRequest | null {
  return rides
    .filter(isRideActive)
    .sort((left, right) => new Date(right.requested_at).getTime() - new Date(left.requested_at).getTime())[0] ?? null;
}

export function sortRidesByRequestedAt(rides: RideRequest[]): RideRequest[] {
  return [...rides].sort((left, right) => new Date(right.requested_at).getTime() - new Date(left.requested_at).getTime());
}

export function canCancelRide(ride: RideRequest): boolean {
  const status = getRideDisplayStatus(ride);

  return status !== "TRIP_COMPLETED" && status !== "CANCELLED";
}

export function getDriverCurrentTrip(trips: Trip[]): Trip | null {
  return [...trips]
    .filter((trip) => trip.status !== "TRIP_COMPLETED" && trip.status !== "CANCELLED")
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime())[0] ?? null;
}

export function getDriverCompletedTrips(trips: Trip[]): Trip[] {
  return [...trips]
    .filter((trip) => trip.status === "TRIP_COMPLETED")
    .sort((left, right) => new Date(right.updated_at).getTime() - new Date(left.updated_at).getTime());
}

export function canTransitionDriverTrip(status: TripStatus, action: "en-route" | "arrived" | "start" | "complete"): boolean {
  switch (action) {
    case "en-route":
      return status === "DRIVER_ASSIGNED";
    case "arrived":
      return status === "DRIVER_EN_ROUTE";
    case "start":
      return status === "DRIVER_ARRIVED";
    case "complete":
      return status === "TRIP_STARTED";
    default:
      return false;
  }
}

export function shouldShowDriverDestination(status: TripStatus): boolean {
  return status === "TRIP_STARTED" || status === "TRIP_COMPLETED";
}

export function validateDriverCoordinates(payload: Pick<DriverAvailabilityPayload, "latitude" | "longitude">): string | null {
  if (Number.isNaN(payload.latitude) || payload.latitude < -90 || payload.latitude > 90) {
    return "Latitude must be between -90 and 90.";
  }

  if (Number.isNaN(payload.longitude) || payload.longitude < -180 || payload.longitude > 180) {
    return "Longitude must be between -180 and 180.";
  }

  return null;
}

export function calculateMetricPercentage(value: number, total: number): string {
  if (total === 0) {
    return "0%";
  }

  return `${Math.round((value / total) * 100)}%`;
}
