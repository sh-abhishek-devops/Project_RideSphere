import { apiClient } from "api/client";
import type { Payment } from "types/models";

export async function getTripPayment(tripId: string): Promise<Payment> {
  const response = await apiClient.get<Payment>(`/api/v1/trips/${tripId}/payment`);
  return response.data;
}

export async function refundPayment(paymentId: string): Promise<Payment> {
  const response = await apiClient.post<Payment>(`/api/v1/payments/${paymentId}/refund`);
  return response.data;
}
