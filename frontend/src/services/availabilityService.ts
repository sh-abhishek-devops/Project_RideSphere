import { apiClient } from "api/client";
import type { DriverAvailability, DriverAvailabilityPayload } from "types/models";

export async function getMyDriverAvailability(): Promise<DriverAvailability> {
  const response = await apiClient.get<DriverAvailability>("/api/v1/drivers/me/availability");
  return response.data;
}

export async function updateMyDriverAvailability(
  payload: DriverAvailabilityPayload
): Promise<DriverAvailability> {
  const response = await apiClient.put<DriverAvailability>("/api/v1/drivers/me/availability", payload);
  return response.data;
}

export async function listDriverAvailabilities(): Promise<DriverAvailability[]> {
  const response = await apiClient.get<DriverAvailability[]>("/api/driver-availabilities");
  return response.data;
}
