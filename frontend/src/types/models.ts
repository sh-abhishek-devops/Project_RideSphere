export type UserRole =
  | "RIDER"
  | "DRIVER"
  | "SUPPORT_AGENT"
  | "PAYMENT_AGENT"
  | "OPERATIONS_MANAGER"
  | "ADMIN";

export type AvailabilityStatus = "OFFLINE" | "AVAILABLE" | "RESERVED" | "ON_TRIP";
export type RideType = "STANDARD" | "XL" | "PREMIUM";
export type RideRequestStatus = "REQUESTED" | "SEARCHING_DRIVER" | "DRIVER_ASSIGNED" | "CANCELLED";
export type TripStatus =
  | "DRIVER_ASSIGNED"
  | "DRIVER_EN_ROUTE"
  | "DRIVER_ARRIVED"
  | "TRIP_STARTED"
  | "TRIP_COMPLETED"
  | "CANCELLED";
export type PaymentStatus = "PENDING" | "PROCESSING" | "SUCCESS" | "FAILED" | "REFUNDED";
export type SupportCasePriority = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type SupportCaseStatus =
  | "OPEN"
  | "ASSIGNED"
  | "INVESTIGATING"
  | "WAITING_ON_RIDER"
  | "WAITING_ON_DRIVER"
  | "RESOLVED";

export interface DatabaseHealthResponse {
  status: string;
  engine: string;
  driver: string;
  host: string;
  port: number;
  database: string;
}

export interface HealthResponse {
  status: string;
  application: string;
  database?: DatabaseHealthResponse;
}

export interface OperationsDashboardMetrics {
  date_from: string | null;
  date_to: string | null;
  total_ride_requests: number;
  rides_searching_for_drivers: number;
  active_trips: number;
  completed_trips: number;
  cancelled_rides: number;
  available_drivers: number;
  drivers_currently_on_trips: number;
  payment_successes: number;
  payment_failures: number;
  open_support_cases: number;
  generated_at: string;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone_number: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Rider {
  id: string;
  user_id: string;
  user: User;
}

export interface Driver {
  id: string;
  user_id: string;
  user: User;
}

export interface Vehicle {
  id: string;
  driver_id: string;
  make: string;
  model: string;
  year: number;
  color: string;
  license_plate: string;
  vehicle_type: string;
  is_active: boolean;
}

export interface DriverAvailability {
  id: string;
  driver_id: string;
  status: AvailabilityStatus;
  latitude: number;
  longitude: number;
  updated_at: string;
}

export interface TripStatusHistory {
  id: string;
  trip_id: string;
  previous_status: TripStatus | null;
  new_status: TripStatus;
  changed_by: string;
  timestamp: string;
}

export interface TripRideRequestSummary {
  id: string;
  pickup_address: string;
  pickup_latitude: number;
  pickup_longitude: number;
  destination_address: string;
  destination_latitude: number;
  destination_longitude: number;
  ride_type: RideType;
}

export interface Trip {
  id: string;
  ride_request_id: string;
  rider_id: string;
  driver_id: string;
  vehicle_id: string | null;
  status: TripStatus;
  started_at: string | null;
  completed_at: string | null;
  actual_distance: number | null;
  actual_duration: number | null;
  created_at: string;
  updated_at: string;
  ride_request: TripRideRequestSummary;
  status_history: TripStatusHistory[];
}

export interface RideRequest {
  id: string;
  rider_id: string;
  driver_id: string | null;
  pickup_address: string;
  pickup_latitude: number;
  pickup_longitude: number;
  destination_address: string;
  destination_latitude: number;
  destination_longitude: number;
  ride_type: RideType;
  requested_at: string;
  status: RideRequestStatus;
  estimated_distance: number;
  estimated_duration: number;
  created_at: string;
  updated_at: string;
  trip: Trip | null;
}

export interface Payment {
  id: string;
  trip_id: string;
  rider_id: string | null;
  amount: number | null;
  currency: string | null;
  status: PaymentStatus;
  payment_reference: string | null;
  created_at: string;
  updated_at: string;
}

export interface SupportAgentSummary {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  is_active: boolean;
}

export interface SupportCase {
  id: string;
  ride_request_id: string;
  trip_id: string | null;
  created_by_user_id: string;
  assigned_agent_user_id: string | null;
  issue_summary: string;
  priority: SupportCasePriority;
  status: SupportCaseStatus;
  resolution_notes: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  created_by_user: SupportAgentSummary;
  assigned_agent_user: SupportAgentSummary | null;
}

export interface SupportInvestigation {
  case: SupportCase;
  rider: Rider;
  driver: Driver | null;
  vehicle: Vehicle | null;
  ride_request: RideRequest;
  trip: Trip | null;
  payment: Payment | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: "bearer";
}

export interface CurrentUserEnvelope {
  user: User;
}

export interface RiderRegistrationResponse {
  rider: Rider;
}

export interface DriverRegistrationResponse {
  driver: Driver;
}

export interface RegisterUserPayload {
  user: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone_number: string;
    is_active: boolean;
  };
}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface CreateRidePayload {
  pickup_address: string;
  pickup_latitude: number;
  pickup_longitude: number;
  destination_address: string;
  destination_latitude: number;
  destination_longitude: number;
  ride_type: RideType;
  estimated_distance: number;
  estimated_duration: number;
}

export interface CompleteTripPayload {
  actual_distance: number;
  actual_duration: number;
}

export interface DriverAvailabilityPayload {
  status: Extract<AvailabilityStatus, "OFFLINE" | "AVAILABLE">;
  latitude: number;
  longitude: number;
}

export interface CreateSupportCasePayload {
  ride_request_id: string;
  issue_summary: string;
  priority: SupportCasePriority;
  assigned_agent_user_id?: string | null;
}

export interface UpdateSupportCasePayload {
  assigned_agent_user_id?: string | null;
  priority?: SupportCasePriority;
  status?: Exclude<SupportCaseStatus, "RESOLVED">;
  resolution_notes?: string | null;
}

export interface ResolveSupportCasePayload {
  resolution_notes: string;
}
