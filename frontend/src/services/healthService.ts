import { apiClient } from "api/client";
import type { HealthResponse } from "types/models";

export async function fetchHealthStatus(): Promise<HealthResponse> {
  const response = await apiClient.get<HealthResponse>("/api/health");
  return response.data;
}
