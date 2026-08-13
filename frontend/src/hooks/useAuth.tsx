import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { clearStoredToken, getStoredToken, setStoredToken } from "api/authStorage";
import { getCurrentUser, loginUser, registerDriver, registerRider } from "services/authService";
import type {
  CurrentUserEnvelope,
  DriverRegistrationResponse,
  LoginPayload,
  RegisterUserPayload,
  RiderRegistrationResponse,
  User,
  UserRole
} from "types/models";

interface AuthContextValue {
  token: string | null;
  user: User | null;
  role: UserRole | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (payload: LoginPayload) => Promise<CurrentUserEnvelope>;
  logout: () => void;
  registerRiderAccount: (payload: RegisterUserPayload) => Promise<RiderRegistrationResponse>;
  registerDriverAccount: (payload: RegisterUserPayload) => Promise<DriverRegistrationResponse>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => getStoredToken());

  const meQuery = useQuery({
    queryKey: ["auth", "me", token],
    queryFn: getCurrentUser,
    enabled: Boolean(token),
    retry: false
  });

  useEffect(() => {
    function handleAuthExpired() {
      clearStoredToken();
      setToken(null);
      queryClient.removeQueries({ queryKey: ["auth"] });
    }

    window.addEventListener("ridesphere:auth-expired", handleAuthExpired);

    return () => {
      window.removeEventListener("ridesphere:auth-expired", handleAuthExpired);
    };
  }, [queryClient]);

  const user = meQuery.data?.user ?? null;

  async function login(payload: LoginPayload): Promise<CurrentUserEnvelope> {
    const result = await loginUser(payload);
    setStoredToken(result.access_token);
    setToken(result.access_token);

    const envelope = await queryClient.fetchQuery({
      queryKey: ["auth", "me", result.access_token],
      queryFn: getCurrentUser
    });

    return envelope;
  }

  function logout(): void {
    clearStoredToken();
    setToken(null);
    queryClient.removeQueries();
  }

  const value: AuthContextValue = {
    token,
    user,
    role: user?.role ?? null,
    isAuthenticated: Boolean(token && user),
    isInitializing: Boolean(token) && meQuery.isLoading,
    login,
    logout,
    registerRiderAccount: registerRider,
    registerDriverAccount: registerDriver
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within AuthProvider.");
  }

  return context;
}
