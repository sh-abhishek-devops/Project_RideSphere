import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { AuthProvider, useAuth } from "./useAuth";

const { getCurrentUser, loginUser, registerDriver, registerRider } = vi.hoisted(() => ({
  getCurrentUser: vi.fn(),
  loginUser: vi.fn(),
  registerDriver: vi.fn(),
  registerRider: vi.fn()
}));

vi.mock("services/authService", () => ({
  getCurrentUser,
  loginUser,
  registerDriver,
  registerRider
}));

function AuthHarness() {
  const auth = useAuth();

  return (
    <div>
      <span>{auth.isAuthenticated ? auth.user?.email : "signed-out"}</span>
      <button
        onClick={() => {
          void auth.login({ email: "rider@example.com", password: "Password123" });
        }}
        type="button"
      >
        Login
      </button>
      <button onClick={() => auth.logout()} type="button">
        Logout
      </button>
    </div>
  );
}

function renderHarness() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <AuthHarness />
      </AuthProvider>
    </QueryClientProvider>
  );
}

describe("useAuth", () => {
  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  it("logs in and clears session when auth expires", async () => {
    loginUser.mockResolvedValue({ access_token: "token-123", token_type: "bearer" });
    getCurrentUser.mockResolvedValue({
      user: {
        id: "user-1",
        email: "rider@example.com",
        first_name: "Rider",
        last_name: "User",
        phone_number: "+15550000000",
        role: "RIDER",
        is_active: true,
        created_at: "2026-08-11T12:00:00Z",
        updated_at: "2026-08-11T12:00:00Z"
      }
    });

    renderHarness();

    expect(screen.getByText("signed-out")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Login" }));

    await waitFor(() => {
      expect(screen.getByText("rider@example.com")).toBeInTheDocument();
    });
    expect(localStorage.getItem("ridesphere.auth.token")).toBe("token-123");

    window.dispatchEvent(new Event("ridesphere:auth-expired"));

    await waitFor(() => {
      expect(screen.getByText("signed-out")).toBeInTheDocument();
    });
    expect(localStorage.getItem("ridesphere.auth.token")).toBeNull();
  });
});
