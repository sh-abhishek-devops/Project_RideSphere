import { useQuery } from "@tanstack/react-query";

import { fetchHealthStatus } from "../services/healthService";

export function useHealthStatus() {
  return useQuery({
    queryKey: ["health-status"],
    queryFn: fetchHealthStatus,
    retry: 1
  });
}
