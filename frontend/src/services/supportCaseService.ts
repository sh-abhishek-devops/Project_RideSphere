import { apiClient } from "api/client";
import type {
  CreateSupportCasePayload,
  ResolveSupportCasePayload,
  SupportAgentSummary,
  SupportCase,
  SupportInvestigation,
  UpdateSupportCasePayload
} from "types/models";

export async function listSupportCases(): Promise<SupportCase[]> {
  const response = await apiClient.get<SupportCase[]>("/api/v1/support/cases");
  return response.data;
}

export async function getSupportCase(caseId: string): Promise<SupportCase> {
  const response = await apiClient.get<SupportCase>(`/api/v1/support/cases/${caseId}`);
  return response.data;
}

export async function createSupportCase(payload: CreateSupportCasePayload): Promise<SupportCase> {
  const response = await apiClient.post<SupportCase>("/api/v1/support/cases", payload);
  return response.data;
}

export async function updateSupportCase(caseId: string, payload: UpdateSupportCasePayload): Promise<SupportCase> {
  const response = await apiClient.patch<SupportCase>(`/api/v1/support/cases/${caseId}`, payload);
  return response.data;
}

export async function resolveSupportCase(caseId: string, payload: ResolveSupportCasePayload): Promise<SupportCase> {
  const response = await apiClient.post<SupportCase>(`/api/v1/support/cases/${caseId}/resolve`, payload);
  return response.data;
}

export async function getSupportInvestigation(caseId: string): Promise<SupportInvestigation> {
  const response = await apiClient.get<SupportInvestigation>(`/api/v1/support/cases/${caseId}/investigation`);
  return response.data;
}

export async function listSupportAgents(): Promise<SupportAgentSummary[]> {
  const response = await apiClient.get<SupportAgentSummary[]>("/api/v1/support/agents");
  return response.data;
}
