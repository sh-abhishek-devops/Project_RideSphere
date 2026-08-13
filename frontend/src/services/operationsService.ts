import { apiClient } from "api/client";
import type { OperationsDashboardMetrics } from "types/models";

export interface OperationsDashboardFilters {
  dateFrom?: string;
  dateTo?: string;
}

export async function getOperationsDashboardMetrics(
  filters: OperationsDashboardFilters
): Promise<OperationsDashboardMetrics> {
  const response = await apiClient.get<OperationsDashboardMetrics>("/api/v1/operations/dashboard", {
    params: {
      date_from: filters.dateFrom || undefined,
      date_to: filters.dateTo || undefined
    }
  });
  return response.data;
}
