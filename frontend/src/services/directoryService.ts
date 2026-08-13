import { apiClient } from "api/client";
import type { Driver, Rider, User, Vehicle } from "types/models";

export async function listUsers(): Promise<User[]> {
  const response = await apiClient.get<User[]>("/api/users");
  return response.data;
}

export async function listRiders(): Promise<Rider[]> {
  const response = await apiClient.get<Rider[]>("/api/riders");
  return response.data;
}

export async function listDrivers(): Promise<Driver[]> {
  const response = await apiClient.get<Driver[]>("/api/drivers");
  return response.data;
}

export async function listVehicles(): Promise<Vehicle[]> {
  const response = await apiClient.get<Vehicle[]>("/api/vehicles");
  return response.data;
}
