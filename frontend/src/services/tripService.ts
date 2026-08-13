import { apiClient } from "api/client";
import type { CompleteTripPayload, StartTripPayload, Trip } from "types/models";

export async function listMyDriverTrips(): Promise<Trip[]> {
  const response = await apiClient.get<Trip[]>("/api/v1/drivers/me/trips");
  return response.data;
}

export async function getTrip(tripId: string): Promise<Trip> {
  const response = await apiClient.get<Trip>(`/api/v1/trips/${tripId}`);
  return response.data;
}

export async function markTripEnRoute(tripId: string): Promise<Trip> {
  const response = await apiClient.post<Trip>(`/api/v1/trips/${tripId}/en-route`);
  return response.data;
}

export async function markTripArrived(tripId: string): Promise<Trip> {
  const response = await apiClient.post<Trip>(`/api/v1/trips/${tripId}/arrived`);
  return response.data;
}

export async function startTrip(tripId: string, payload: StartTripPayload): Promise<Trip> {
  const response = await apiClient.post<Trip>(`/api/v1/trips/${tripId}/start`, payload);
  return response.data;
}

export async function completeTrip(tripId: string, payload: CompleteTripPayload): Promise<Trip> {
  const response = await apiClient.post<Trip>(`/api/v1/trips/${tripId}/complete`, payload);
  return response.data;
}
