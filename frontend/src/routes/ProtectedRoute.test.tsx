import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ProtectedRoute } from "./ProtectedRoute";

const { useAuth } = vi.hoisted(() => ({
  useAuth: vi.fn()
}));

vi.mock("hooks/useAuth", () => ({
  useAuth
}));

function renderRoutes(initialPath = "/protected") {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<ProtectedRoute allowedRoles={["ADMIN"]} />}>
          <Route path="/protected" element={<div>Protected content</div>} />
        </Route>
        <Route path="/login" element={<div>Login page</div>} />
        <Route path="/unauthorized" element={<div>Unauthorized page</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("ProtectedRoute", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("redirects unauthenticated users to login", async () => {
    useAuth.mockReturnValue({
      isInitializing: false,
      isAuthenticated: false,
      role: null
    });

    renderRoutes();

    expect(await screen.findByText("Login page")).toBeInTheDocument();
  });

  it("redirects unauthorized users to unauthorized page", async () => {
    useAuth.mockReturnValue({
      isInitializing: false,
      isAuthenticated: true,
      role: "RIDER"
    });

    renderRoutes();

    expect(await screen.findByText("Unauthorized page")).toBeInTheDocument();
  });

  it("renders content for allowed roles", async () => {
    useAuth.mockReturnValue({
      isInitializing: false,
      isAuthenticated: true,
      role: "ADMIN"
    });

    renderRoutes();

    expect(await screen.findByText("Protected content")).toBeInTheDocument();
  });
});
