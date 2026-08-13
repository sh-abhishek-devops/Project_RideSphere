import { apiClient } from "api/client";
import type { CreateRidePayload, RideRequest } from "types/models";

export async function listRides(): Promise<RideRequest[]> {
  const response = await apiClient.get<RideRequest[]>("/api/v1/rides");
  return response.data;
}

export async function getRide(rideId: string): Promise<RideRequest> {
  const response = await apiClient.get<RideRequest>(`/api/v1/rides/${rideId}`);
  return response.data;
}

export async function createRide(payload: CreateRidePayload): Promise<RideRequest> {
  const response = await apiClient.post<RideRequest>("/api/v1/rides", payload);
  return response.data;
}

export async function cancelRide(rideId: string): Promise<RideRequest> {
  const response = await apiClient.post<RideRequest>(`/api/v1/rides/${rideId}/cancel`);
  return response.data;
}

export async function listDriverRideOffers(): Promise<RideRequest[]> {
  const response = await apiClient.get<RideRequest[]>("/api/v1/drivers/me/ride-offers");
  return response.data;
}

export async function acceptDriverRideOffer(rideId: string): Promise<RideRequest> {
  const response = await apiClient.post<RideRequest>(`/api/v1/drivers/me/ride-offers/${rideId}/accept`);
  return response.data;
}
