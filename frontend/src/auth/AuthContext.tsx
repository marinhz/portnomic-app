import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import api, {
  setTokens,
  clearTokens,
  getAccessToken,
  ApiError,
} from "@/api/client";
import type { CurrentUser, LoginResponse } from "@/api/types";

type LoginResult =
  | { success: true }
  | { requiresMfa: true; mfaToken: string }
  | { success: false; error: string };

type MfaResult = { success: true } | { success: false; error: string };

function getLoginErrorMessage(err: unknown, fallback: string): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (err as { response?: { data?: unknown; status?: number } }).response;
    const data = res?.data;
    const status = res?.status;
    if (data && typeof data === "object") {
      const d = data as { error?: { message?: string }; message?: string };
      const msg = d.error?.message ?? d.message;
      if (typeof msg === "string" && msg.trim()) return msg;
    }
    if (status === 401) return "Invalid email or password";
  }
  return fallback;
}

type AuthContextType = {
  user: CurrentUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  logout: () => void;
  completeMfa: (mfaToken: string, code: string) => Promise<MfaResult>;
  refreshUser: () => Promise<void>;
};

const AuthContext = createContext<AuthContextType | null>(null);

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const resp = await api.get<{ data: CurrentUser }>("/auth/me");
      setUser(resp.data.data);
      return true;
    } catch {
      setUser(null);
      return false;
    }
  }, []);

  useEffect(() => {
    if (getAccessToken()) {
      fetchCurrentUser().then((ok) => {
        if (!ok) clearTokens();
        setIsLoading(false);
      });
    } else {
      setIsLoading(false);
    }
  }, [fetchCurrentUser]);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      try {
        const { data } = await api.post<LoginResponse>("/auth/login", {
          email,
          password,
        });

        if (data.requires_mfa && data.mfa_token) {
          return { requiresMfa: true, mfaToken: data.mfa_token };
        }

        if (data.access_token && data.refresh_token) {
          setTokens(data.access_token, data.refresh_token);
          await fetchCurrentUser();
          return { success: true };
        }

        return { success: false, error: "Unexpected response from server" };
      } catch (err) {
        const message = err instanceof ApiError
          ? err.message
          : getLoginErrorMessage(err, "Login failed");
        return { success: false, error: message };
      }
    },
    [fetchCurrentUser],
  );

  const completeMfa = useCallback(
    async (mfaToken: string, code: string): Promise<MfaResult> => {
      try {
        const { data } = await api.post<LoginResponse>("/auth/mfa", {
          mfa_token: mfaToken,
          code,
        });
        setTokens(data.access_token, data.refresh_token);
        await fetchCurrentUser();
        return { success: true };
      } catch (err) {
        const message = err instanceof ApiError
          ? err.message
          : getLoginErrorMessage(err, "MFA verification failed");
        return { success: false, error: message };
      }
    },
    [fetchCurrentUser],
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  const refreshUser = useCallback(async () => {
    await fetchCurrentUser();
  }, [fetchCurrentUser]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        completeMfa,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
