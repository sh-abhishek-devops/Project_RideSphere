import { apiClient } from "api/client";
import type {
  CurrentUserEnvelope,
  DriverRegistrationResponse,
  LoginPayload,
  LoginResponse,
  RegisterUserPayload,
  RiderRegistrationResponse
} from "types/models";

export async function loginUser(payload: LoginPayload): Promise<LoginResponse> {
  const formData = new URLSearchParams();
  formData.set("username", payload.email);
  formData.set("password", payload.password);

  const response = await apiClient.post<LoginResponse>("/api/v1/auth/login", formData, {
    headers: {
      "Content-Type": "application/x-www-form-urlencoded"
    }
  });

  return response.data;
}

export async function registerRider(payload: RegisterUserPayload): Promise<RiderRegistrationResponse> {
  const response = await apiClient.post<RiderRegistrationResponse>("/api/v1/auth/register/rider", payload);
  return response.data;
}

export async function registerDriver(payload: RegisterUserPayload): Promise<DriverRegistrationResponse> {
  const response = await apiClient.post<DriverRegistrationResponse>("/api/v1/auth/register/driver", payload);
  return response.data;
}

export async function getCurrentUser(): Promise<CurrentUserEnvelope> {
  const response = await apiClient.get<CurrentUserEnvelope>("/api/v1/auth/me");
  return response.data;
}
