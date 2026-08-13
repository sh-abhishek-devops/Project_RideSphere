const TOKEN_STORAGE_KEY = "ridesphere.auth.token";
const DRIVER_TRIP_STORAGE_KEY = "ridesphere.driver.tripId";

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function getStoredDriverTripId(): string {
  return localStorage.getItem(DRIVER_TRIP_STORAGE_KEY) ?? "";
}

export function setStoredDriverTripId(tripId: string): void {
  localStorage.setItem(DRIVER_TRIP_STORAGE_KEY, tripId);
}

export function clearStoredDriverTripId(): void {
  localStorage.removeItem(DRIVER_TRIP_STORAGE_KEY);
}
